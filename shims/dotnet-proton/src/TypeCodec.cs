/*
 * QIT .NET Apache Qpid Proton Shim - Type Codec
 *
 * Handles encoding/decoding between JSON test values and AMQP types
 */

using System;
using System.Globalization;
using System.Text;
using Apache.Qpid.Proton.Types;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;

namespace Qit.Shim
{
    public static class TypeCodec
    {
        /// <summary>
        /// Encode JSON value to AMQP object
        /// </summary>
        public static object Encode(string amqpType, object value)
        {
            // Handle JToken input
            if (value is JToken jtoken)
            {
                if (jtoken.Type == JTokenType.Null || jtoken == null)
                {
                    return null!;
                }
                value = jtoken.ToObject<object>();
            }

            switch (amqpType)
            {
                case "null":
                    return null!;

                case "boolean":
                    if (value is bool bval) return bval;
                    var strVal = value?.ToString() ?? "false";
                    return strVal.Equals("True", StringComparison.OrdinalIgnoreCase) ||
                           strVal.Equals("true", StringComparison.OrdinalIgnoreCase);

                case "ubyte":
                    return (byte)ParseUInt(value);

                case "ushort":
                    return (ushort)ParseUInt(value);

                case "uint":
                    return (uint)ParseUInt(value);

                case "ulong":
                    return ParseUInt(value);

                case "byte":
                    return (sbyte)ParseInt(value);

                case "short":
                    return (short)ParseInt(value);

                case "int":
                    return (int)ParseInt(value);

                case "long":
                    return ParseInt(value);

                case "float":
                    return ParseFloat(value);

                case "double":
                    return ParseDouble(value);

                case "char":
                    var codePoint = Convert.ToInt32(value);
                    return (char)codePoint;

                case "timestamp":
                    var millis = Convert.ToInt64(value);
                    return new DateTime(1970, 1, 1, 0, 0, 0, DateTimeKind.Utc).AddMilliseconds(millis);

                case "uuid":
                    var uuidStr = value?.ToString() ?? "";
                    return Guid.Parse(uuidStr);

                case "binary":
                    var hexStr = value?.ToString() ?? "";
                    return HexToBytes(hexStr);

                case "string":
                    return value?.ToString() ?? "";

                case "symbol":
                    // Create a Symbol object to preserve type information
                    return Symbol.Lookup(value?.ToString() ?? "");

                default:
                    throw new NotSupportedException($"Unsupported AMQP type: {amqpType}");
            }
        }

        /// <summary>
        /// Decode AMQP object to typed result
        /// </summary>
        public static DecodedMessage Decode(object value)
        {
            if (value == null)
            {
                return new DecodedMessage { Type = "null", Value = null };
            }

            string qpiditType = InferType(value);

            object resultValue = qpiditType switch
            {
                "null" => null!,
                "boolean" => (bool)value,
                "ubyte" => (byte)value,
                "ushort" => (ushort)value,
                "uint" => (uint)value,
                "ulong" => (ulong)value,
                "byte" => (sbyte)value,
                "short" => (short)value,
                "int" => (int)value,
                "long" => (long)value,
                "float" => FormatFloatAsHex((float)value),
                "double" => FormatDoubleAsHex((double)value),
                "char" => (int)(char)value,
                "timestamp" => ConvertToEpochMillis((DateTime)value),
                "uuid" => ((Guid)value).ToString(),
                "binary" => BytesToHex((byte[])value),
                "string" => (string)value,
                "symbol" => value.ToString()!,
                _ => value.ToString()!
            };

            return new DecodedMessage
            {
                Type = qpiditType,
                Value = resultValue
            };
        }

        /// <summary>
        /// Infer AMQP type name from .NET object using reflection
        /// </summary>
        private static string InferType(object obj)
        {
            if (obj == null) return "null";

            var type = obj.GetType();
            var typeName = type.Name;

            // For Qpid Proton .NET, symbols might be a special type
            // We'll check namespace as well
            if (type.Namespace?.Contains("Qpid.Proton") == true)
            {
                if (typeName.Contains("Symbol", StringComparison.OrdinalIgnoreCase))
                    return "symbol";
            }

            return typeName switch
            {
                "Boolean" => "boolean",
                "Byte" => "ubyte",
                "UInt16" => "ushort",
                "UInt32" => "uint",
                "UInt64" => "ulong",
                "SByte" => "byte",
                "Int16" => "short",
                "Int32" => "int",
                "Int64" => "long",
                "Single" => "float",
                "Double" => "double",
                "Char" => "char",
                "DateTime" => "timestamp",
                "Guid" => "uuid",
                "Byte[]" => "binary",
                "String" => "string",
                _ => "unknown"
            };
        }

        // Helper methods

        private static ulong ParseUInt(object value)
        {
            if (value is ulong ul) return ul;
            if (value is long l) return (ulong)l;

            var str = value?.ToString() ?? "0";
            if (str.StartsWith("0x", StringComparison.OrdinalIgnoreCase))
                return ulong.Parse(str.Substring(2), NumberStyles.HexNumber);

            return ulong.Parse(str);
        }

        private static long ParseInt(object value)
        {
            if (value is long l) return l;
            if (value is int i) return i;

            var str = value?.ToString() ?? "0";
            if (str.StartsWith("-0x", StringComparison.OrdinalIgnoreCase))
                return -((long)ulong.Parse(str.Substring(3), NumberStyles.HexNumber));
            if (str.StartsWith("0x", StringComparison.OrdinalIgnoreCase))
                return (long)ulong.Parse(str.Substring(2), NumberStyles.HexNumber);

            return long.Parse(str);
        }

        private static float ParseFloat(object value)
        {
            if (value is float f) return f;

            var str = value?.ToString() ?? "0.0";
            if (str.StartsWith("0x", StringComparison.OrdinalIgnoreCase))
            {
                // Hex representation
                var intVal = uint.Parse(str.Substring(2), NumberStyles.HexNumber);
                var bytes = BitConverter.GetBytes(intVal);
                return BitConverter.ToSingle(bytes, 0);
            }

            return float.Parse(str, CultureInfo.InvariantCulture);
        }

        private static double ParseDouble(object value)
        {
            if (value is double d) return d;

            var str = value?.ToString() ?? "0.0";
            if (str.StartsWith("0x", StringComparison.OrdinalIgnoreCase))
            {
                // Hex representation
                var intVal = ulong.Parse(str.Substring(2), NumberStyles.HexNumber);
                var bytes = BitConverter.GetBytes(intVal);
                return BitConverter.ToDouble(bytes, 0);
            }

            return double.Parse(str, CultureInfo.InvariantCulture);
        }

        private static string FormatFloatAsHex(float value)
        {
            var bytes = BitConverter.GetBytes(value);
            var intVal = BitConverter.ToUInt32(bytes, 0);
            return $"0x{intVal:x8}";
        }

        private static string FormatDoubleAsHex(double value)
        {
            var bytes = BitConverter.GetBytes(value);
            var longVal = BitConverter.ToUInt64(bytes, 0);
            return $"0x{longVal:x16}";
        }

        private static long ConvertToEpochMillis(DateTime dt)
        {
            var epoch = new DateTime(1970, 1, 1, 0, 0, 0, DateTimeKind.Utc);
            return (long)(dt.ToUniversalTime() - epoch).TotalMilliseconds;
        }

        private static byte[] HexToBytes(string hex)
        {
            var bytes = new byte[hex.Length / 2];
            for (int i = 0; i < bytes.Length; i++)
            {
                bytes[i] = byte.Parse(hex.Substring(i * 2, 2), NumberStyles.HexNumber);
            }
            return bytes;
        }

        private static string BytesToHex(byte[] bytes)
        {
            var sb = new StringBuilder();
            foreach (var b in bytes)
            {
                sb.Append(b.ToString("x2"));
            }
            return sb.ToString();
        }
    }

    public class DecodedMessage
    {
        [JsonProperty("type")]
        public string Type { get; set; } = "";

        [JsonProperty("value")]
        public object? Value { get; set; }
    }
}
