// adapters.rs - serde adapters and helpers
//
// Contains serialization helpers used by domain types. Keeping adapters in a
// separate module keeps `types` focused on domain semantics while making the
// serializers reusable from other modules.

use base64::Engine;
use bytes::Bytes;
use serde::{self, Deserialize, Deserializer, Serializer};

/// Serialize/deserialize `Bytes` as base64 strings when embedded into JSON.
///
/// Reasoning: binary payloads are opaque (blobs). When returning events or
/// logging them as JSON we must ensure the resulting JSON is valid. Base64 is
/// a compact, portable representation and commonly used for this purpose.
pub mod base64_bytes {
    use super::*;

    /// Serialize `Bytes` as a base64 string.
    pub fn serialize<S>(b: &Bytes, s: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        let encoded = base64::engine::general_purpose::STANDARD.encode(b.as_ref());
        s.serialize_str(&encoded)
    }

    /// Deserialize a base64 string into `Bytes`.
    pub fn deserialize<'de, D>(d: D) -> Result<Bytes, D::Error>
    where
        D: Deserializer<'de>,
    {
        let s = String::deserialize(d)?;
        let decoded = base64::engine::general_purpose::STANDARD
            .decode(&s)
            .map_err(serde::de::Error::custom)?;
        Ok(Bytes::from(decoded))
    }
}
