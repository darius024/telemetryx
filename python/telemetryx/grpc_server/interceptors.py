"""gRPC server interceptors for cross-cutting concerns.

Interceptors handle logging, metrics, and other middleware functionality.
"""

import time
from typing import Any, Callable, Awaitable

import grpc

from telemetryx.core import get_logger


class LoggingInterceptor(grpc.aio.ServerInterceptor):
    """Interceptor that logs all RPC requests and responses.
    
    Logs:
    - Method name
    - Request duration
    - Status code
    - Any errors
    """

    def __init__(self) -> None:
        self._logger = get_logger(__name__, component="grpc-interceptor")

    async def intercept_service(
        self,
        continuation: Callable[
            [grpc.HandlerCallDetails],
            Awaitable[grpc.RpcMethodHandler],
        ],
        handler_call_details: grpc.HandlerCallDetails,
    ) -> grpc.RpcMethodHandler:
        """Intercept and log RPC calls.
        
        Args:
            continuation: The next interceptor or handler
            handler_call_details: Details about the RPC call
            
        Returns:
            The RPC method handler (possibly wrapped)
        """
        method = handler_call_details.method
        
        # Get the actual handler
        handler = await continuation(handler_call_details)
        
        if handler is None:
            return handler

        # Wrap unary-unary handlers
        if handler.unary_unary:
            return grpc.unary_unary_rpc_method_handler(
                self._wrap_unary_unary(handler.unary_unary, method),
                request_deserializer=handler.request_deserializer,
                response_serializer=handler.response_serializer,
            )

        # Return other handler types as-is for now
        return handler

    def _wrap_unary_unary(
        self,
        behavior: Callable[..., Any],
        method: str,
    ) -> Callable[..., Awaitable[Any]]:
        """Wrap a unary-unary handler with logging.
        
        Args:
            behavior: The original handler function
            method: The RPC method name
            
        Returns:
            Wrapped handler function
        """
        async def wrapper(
            request: Any,
            context: grpc.aio.ServicerContext,
        ) -> Any:
            start_time = time.perf_counter()
            status = "OK"
            error_msg = None

            try:
                response = await behavior(request, context)
                return response
            except grpc.RpcError as e:
                status = e.code().name
                error_msg = str(e.details())
                raise
            except Exception as e:
                status = "INTERNAL"
                error_msg = str(e)
                raise
            finally:
                elapsed_ms = (time.perf_counter() - start_time) * 1000
                
                log_data = {
                    "method": method,
                    "status": status,
                    "duration_ms": round(elapsed_ms, 2),
                }
                
                if error_msg:
                    log_data["error"] = error_msg
                    self._logger.error("RPC failed", **log_data)
                else:
                    self._logger.info("RPC completed", **log_data)

        return wrapper
