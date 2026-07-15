/*
 * QIT ProtonJ2 Shim - Type Codec
 * 
 * Handles encoding/decoding between JSON test values and AMQP types
 */
package org.apache.qpid.qit;

import com.google.gson.JsonElement;
import com.google.gson.JsonPrimitive;
import org.apache.qpid.protonj2.types.Binary;
import org.apache.qpid.protonj2.types.Symbol;
import org.apache.qpid.protonj2.types.UnsignedByte;
import org.apache.qpid.protonj2.types.UnsignedInteger;
import org.apache.qpid.protonj2.types.UnsignedLong;
import org.apache.qpid.protonj2.types.UnsignedShort;

import java.nio.ByteBuffer;
import java.util.Date;
import java.util.UUID;

public class TypeCodec {

    /**
     * Encode JSON test value to AMQP type
     */
    public static Object encode(String amqpType, Object value) throws Exception {
        // Extract value from JsonElement if needed
        if (value instanceof JsonElement) {
            JsonElement jsonValue = (JsonElement) value;
            if (jsonValue.isJsonNull()) {
                return null;
            }
            if (jsonValue.isJsonPrimitive()) {
                JsonPrimitive prim = jsonValue.getAsJsonPrimitive();
                if (prim.isNumber()) {
                    value = prim.getAsLong();
                } else if (prim.isString()) {
                    value = prim.getAsString();
                } else if (prim.isBoolean()) {
                    value = prim.getAsBoolean();
                }
            }
        }

        switch (amqpType) {
            case "null":
                return null;

            case "boolean":
                if (value instanceof Boolean) return (Boolean) value;
                String strVal = value.toString();
                return "True".equalsIgnoreCase(strVal) || "true".equalsIgnoreCase(strVal);

            case "ubyte":
                return UnsignedByte.valueOf(parseLong(value).byteValue());

            case "ushort":
                return UnsignedShort.valueOf(parseLong(value).shortValue());

            case "uint":
                return UnsignedInteger.valueOf(parseLong(value));

            case "ulong":
                return UnsignedLong.valueOf(parseLong(value));

            case "byte":
                return parseLong(value).byteValue();

            case "short":
                return parseLong(value).shortValue();

            case "int":
                return parseLong(value).intValue();

            case "long":
                return parseLong(value);

            case "float":
                return parseFloat(value);

            case "double":
                return parseDouble(value);

            case "char":
                int codePoint = Integer.parseInt(value.toString());
                return codePoint;

            case "timestamp":
                long millis = Long.parseLong(value.toString());
                return new Date(millis);

            case "uuid":
                String uuidStr = value.toString();
                return UUID.fromString(uuidStr);

            case "binary":
                String hexStr = value.toString();
                return new Binary(hexToBytes(hexStr));

            case "string":
                return value.toString();

            case "symbol":
                return Symbol.valueOf(value.toString());

            default:
                throw new IllegalArgumentException("Unsupported AMQP type: " + amqpType);
        }
    }

    /**
     * Decode AMQP value to JSON-compatible format
     */
    public static DecodedMessage decode(Object value) {
        DecodedMessage result = new DecodedMessage();

        if (value == null) {
            result.type = "null";
            result.value = com.google.gson.JsonNull.INSTANCE;
            return result;
        }

        String typeName = inferType(value);
        result.type = typeName;

        switch (typeName) {
            case "null":
                result.value = com.google.gson.JsonNull.INSTANCE;
                break;

            case "boolean":
                result.value = new JsonPrimitive((Boolean) value);
                break;

            case "ubyte":
                result.value = new JsonPrimitive(((UnsignedByte) value).intValue());
                break;

            case "ushort":
                result.value = new JsonPrimitive(((UnsignedShort) value).intValue());
                break;

            case "uint":
                result.value = new JsonPrimitive(((UnsignedInteger) value).longValue());
                break;

            case "ulong":
                result.value = new JsonPrimitive(((UnsignedLong) value).longValue());
                break;

            case "byte":
                result.value = new JsonPrimitive((Byte) value);
                break;

            case "short":
                result.value = new JsonPrimitive((Short) value);
                break;

            case "int":
                result.value = new JsonPrimitive((Integer) value);
                break;

            case "long":
                result.value = new JsonPrimitive((Long) value);
                break;

            case "float":
                result.value = new JsonPrimitive(formatFloatAsHex((Float) value));
                break;

            case "double":
                result.value = new JsonPrimitive(formatDoubleAsHex((Double) value));
                break;

            case "char":
                result.value = new JsonPrimitive((Integer) value);
                break;

            case "timestamp":
                result.value = new JsonPrimitive(((Date) value).getTime());
                break;

            case "uuid":
                result.value = new JsonPrimitive(((UUID) value).toString());
                break;

            case "binary":
                result.value = new JsonPrimitive(bytesToHex(((Binary) value).asByteArray()));
                break;

            case "string":
                result.value = new JsonPrimitive((String) value);
                break;

            case "symbol":
                result.value = new JsonPrimitive(((Symbol) value).toString());
                break;

            default:
                result.value = new JsonPrimitive(value.toString());
                break;
        }

        return result;
    }

    /**
     * Infer AMQP type name from Java object
     */
    private static String inferType(Object obj) {
        if (obj == null) return "null";

        Class<?> clazz = obj.getClass();
        String className = clazz.getSimpleName();

        if (obj instanceof UnsignedByte) return "ubyte";
        if (obj instanceof UnsignedShort) return "ushort";
        if (obj instanceof UnsignedInteger) return "uint";
        if (obj instanceof UnsignedLong) return "ulong";
        if (obj instanceof Byte) return "byte";
        if (obj instanceof Short) return "short";
        if (obj instanceof Integer) return "char";  // Could be int or char - default to char for single values
        if (obj instanceof Long) return "long";
        if (obj instanceof Float) return "float";
        if (obj instanceof Double) return "double";
        if (obj instanceof Boolean) return "boolean";
        if (obj instanceof Date) return "timestamp";
        if (obj instanceof UUID) return "uuid";
        if (obj instanceof Binary) return "binary";
        if (obj instanceof String) return "string";
        if (obj instanceof Symbol) return "symbol";

        return "unknown";
    }

    // Helper methods

    private static Long parseLong(Object value) {
        if (value instanceof Long) return (Long) value;
        if (value instanceof Integer) return ((Integer) value).longValue();

        String str = value.toString();
        if (str.startsWith("-0x") || str.startsWith("-0X")) {
            return -Long.parseLong(str.substring(3), 16);
        }
        if (str.startsWith("0x") || str.startsWith("0X")) {
            return Long.parseLong(str.substring(2), 16);
        }
        return Long.parseLong(str);
    }

    private static Float parseFloat(Object value) {
        if (value instanceof Float) return (Float) value;

        String str = value.toString();
        if (str.startsWith("0x") || str.startsWith("0X")) {
            // Hex representation
            long intVal = Long.parseLong(str.substring(2), 16);
            return Float.intBitsToFloat((int) intVal);
        }
        return Float.parseFloat(str);
    }

    private static Double parseDouble(Object value) {
        if (value instanceof Double) return (Double) value;

        String str = value.toString();
        if (str.startsWith("0x") || str.startsWith("0X")) {
            // Hex representation - use parseUnsignedLong to handle values > Long.MAX_VALUE
            long longVal = Long.parseUnsignedLong(str.substring(2), 16);
            return Double.longBitsToDouble(longVal);
        }
        return Double.parseDouble(str);
    }

    private static String formatFloatAsHex(float value) {
        int bits = Float.floatToRawIntBits(value);
        return String.format("0x%08x", bits);
    }

    private static String formatDoubleAsHex(double value) {
        long bits = Double.doubleToRawLongBits(value);
        return String.format("0x%016x", bits);
    }

    private static byte[] hexToBytes(String hex) {
        int len = hex.length();
        byte[] data = new byte[len / 2];
        for (int i = 0; i < len; i += 2) {
            data[i / 2] = (byte) ((Character.digit(hex.charAt(i), 16) << 4)
                                + Character.digit(hex.charAt(i+1), 16));
        }
        return data;
    }

    private static String bytesToHex(byte[] bytes) {
        StringBuilder sb = new StringBuilder();
        for (byte b : bytes) {
            sb.append(String.format("%02x", b));
        }
        return sb.toString();
    }

    /**
     * Decoded message result
     */
    public static class DecodedMessage {
        public String type;
        public JsonElement value;
    }
}
