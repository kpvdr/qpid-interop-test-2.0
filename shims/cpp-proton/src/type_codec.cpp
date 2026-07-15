/*
 * QIT C++ Proton Shim - Type Codec Implementation
 *
 * Handles encoding/decoding between JSON test values and AMQP types
 */

#include "qit_shim.hpp"
#include <json/json.h>
#include <sstream>
#include <iomanip>
#include <cstring>
#include <stdexcept>

namespace qit {

// Helper: Parse hex string to integer
template<typename T>
T parse_hex(const std::string& hex_str) {
    std::istringstream iss(hex_str);
    T value;
    iss >> std::hex >> value;
    return value;
}

// Helper: Parse hex string to float/double via bit reinterpretation
template<typename FloatT, typename IntT>
FloatT parse_hex_float(const std::string& hex_str) {
    IntT int_val = parse_hex<IntT>(hex_str);
    FloatT float_val;
    std::memcpy(&float_val, &int_val, sizeof(FloatT));
    return float_val;
}

// Helper: Convert float/double to hex string
template<typename FloatT, typename IntT>
std::string float_to_hex(FloatT value) {
    IntT int_val;
    std::memcpy(&int_val, &value, sizeof(FloatT));
    std::ostringstream oss;
    oss << "0x" << std::hex << std::setw(sizeof(IntT) * 2) << std::setfill('0') << int_val;
    return oss.str();
}

// Helper: Convert binary to hex string
std::string binary_to_hex(const proton::binary& bin) {
    std::ostringstream oss;
    for (auto byte : bin) {
        oss << std::hex << std::setw(2) << std::setfill('0')
            << (static_cast<unsigned int>(static_cast<unsigned char>(byte)));
    }
    return oss.str();
}

// Helper: Parse hex string to binary
proton::binary hex_to_binary(const std::string& hex_str) {
    proton::binary result;
    for (size_t i = 0; i < hex_str.length(); i += 2) {
        std::string byte_str = hex_str.substr(i, 2);
        uint8_t byte = static_cast<uint8_t>(std::stoul(byte_str, nullptr, 16));
        result.push_back(static_cast<char>(byte));
    }
    return result;
}

// Encode JSON value to AMQP proton::value
proton::value TypeCodec::encode(const std::string& amqp_type, const Json::Value& test_value) {
    // Get the actual value (it might be wrapped in an object with "value" field)
    const Json::Value& val = test_value.isObject() && test_value.isMember("value")
                              ? test_value["value"]
                              : test_value;

    if (amqp_type == "null") {
        return proton::value();
    }

    if (amqp_type == "boolean") {
        if (val.isBool()) {
            return val.asBool();
        }
        std::string str_val = val.asString();
        return (str_val == "True" || str_val == "true");
    }

    // Integer types - accept both decimal and hex
    if (amqp_type == "ubyte") {
        if (val.isString()) {
            std::string str = val.asString();
            return static_cast<uint8_t>(str.find("0x") == 0 ? parse_hex<unsigned int>(str) : std::stoul(str));
        }
        return static_cast<uint8_t>(val.asUInt());
    }

    if (amqp_type == "ushort") {
        if (val.isString()) {
            std::string str = val.asString();
            return static_cast<uint16_t>(str.find("0x") == 0 ? parse_hex<unsigned int>(str) : std::stoul(str));
        }
        return static_cast<uint16_t>(val.asUInt());
    }

    if (amqp_type == "uint") {
        if (val.isString()) {
            std::string str = val.asString();
            return static_cast<uint32_t>(str.find("0x") == 0 ? parse_hex<uint32_t>(str) : std::stoul(str));
        }
        return static_cast<uint32_t>(val.asUInt());
    }

    if (amqp_type == "ulong") {
        if (val.isString()) {
            std::string str = val.asString();
            return static_cast<uint64_t>(str.find("0x") == 0 ? parse_hex<uint64_t>(str) : std::stoull(str));
        }
        return static_cast<uint64_t>(val.asUInt64());
    }

    if (amqp_type == "byte") {
        if (val.isString()) {
            std::string str = val.asString();
            return static_cast<int8_t>(str.find("0x") == 0 ? parse_hex<int>(str) : std::stoi(str));
        }
        return static_cast<int8_t>(val.asInt());
    }

    if (amqp_type == "short") {
        if (val.isString()) {
            std::string str = val.asString();
            return static_cast<int16_t>(str.find("0x") == 0 ? parse_hex<int>(str) : std::stoi(str));
        }
        return static_cast<int16_t>(val.asInt());
    }

    if (amqp_type == "int") {
        if (val.isString()) {
            std::string str = val.asString();
            return static_cast<int32_t>(str.find("0x") == 0 ? parse_hex<int32_t>(str) : std::stoi(str));
        }
        return static_cast<int32_t>(val.asInt());
    }

    if (amqp_type == "long") {
        if (val.isString()) {
            std::string str = val.asString();
            return static_cast<int64_t>(str.find("0x") == 0 ? parse_hex<int64_t>(str) : std::stoll(str));
        }
        return static_cast<int64_t>(val.asInt64());
    }

    // Floating point - handle hex representation
    if (amqp_type == "float") {
        std::string str_val = val.asString();
        if (str_val.find("0x") == 0) {
            return parse_hex_float<float, uint32_t>(str_val);
        }
        return std::stof(str_val);
    }

    if (amqp_type == "double") {
        std::string str_val = val.asString();
        if (str_val.find("0x") == 0) {
            return parse_hex_float<double, uint64_t>(str_val);
        }
        return std::stod(str_val);
    }

    // Character
    if (amqp_type == "char") {
        int code_point = val.asInt();
        return static_cast<wchar_t>(code_point);
    }

    // Timestamp (milliseconds since epoch)
    if (amqp_type == "timestamp") {
        int64_t millis = val.asInt64();
        return proton::timestamp(millis);
    }

    // UUID
    if (amqp_type == "uuid") {
        std::string uuid_str = val.asString();
        // Parse UUID string (format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx)
        std::string hex_only;
        for (char c : uuid_str) {
            if (c != '-') hex_only += c;
        }
        proton::binary uuid_bytes = hex_to_binary(hex_only);
        proton::uuid uuid;
        if (uuid_bytes.size() == 16) {
            std::memcpy(uuid.begin(), uuid_bytes.data(), 16);
        }
        return uuid;
    }

    // Binary
    if (amqp_type == "binary") {
        std::string hex_str = val.asString();
        return hex_to_binary(hex_str);
    }

    // String
    if (amqp_type == "string") {
        return val.asString();
    }

    // Symbol
    if (amqp_type == "symbol") {
        return proton::symbol(val.asString());
    }

    throw std::runtime_error("Unsupported AMQP type: " + amqp_type);
}

// Decode AMQP proton::value to JSON
Json::Value TypeCodec::decode(const proton::value& val) {
    Json::Value result;

    // Detect type
    std::string type_name = infer_type(val);
    result["type"] = type_name;

    // Decode value based on type
    switch (val.type()) {
        case proton::NULL_TYPE:
            result["value"] = Json::Value::null;
            break;

        case proton::BOOLEAN:
            result["value"] = proton::get<bool>(val);
            break;

        case proton::UBYTE:
            result["value"] = proton::get<uint8_t>(val);
            break;

        case proton::USHORT:
            result["value"] = proton::get<uint16_t>(val);
            break;

        case proton::UINT:
            result["value"] = proton::get<uint32_t>(val);
            break;

        case proton::ULONG:
            result["value"] = static_cast<Json::Value::UInt64>(proton::get<uint64_t>(val));
            break;

        case proton::BYTE:
            result["value"] = proton::get<int8_t>(val);
            break;

        case proton::SHORT:
            result["value"] = proton::get<int16_t>(val);
            break;

        case proton::INT:
            result["value"] = proton::get<int32_t>(val);
            break;

        case proton::LONG:
            result["value"] = static_cast<Json::Value::Int64>(proton::get<int64_t>(val));
            break;

        case proton::FLOAT:
            // Return as hex string for exact comparison
            result["value"] = float_to_hex<float, uint32_t>(proton::get<float>(val));
            break;

        case proton::DOUBLE:
            // Return as hex string for exact comparison
            result["value"] = float_to_hex<double, uint64_t>(proton::get<double>(val));
            break;

        case proton::CHAR: {
            wchar_t c = proton::get<wchar_t>(val);
            result["value"] = static_cast<int>(c);
            break;
        }

        case proton::TIMESTAMP:
            result["value"] = static_cast<Json::Value::Int64>(proton::get<proton::timestamp>(val).milliseconds());
            break;

        case proton::UUID: {
            proton::uuid uuid_val = proton::get<proton::uuid>(val);
            std::ostringstream oss;
            // Format as: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
            const uint8_t* bytes = reinterpret_cast<const uint8_t*>(uuid_val.begin());
            oss << std::hex << std::setfill('0');
            for (int i = 0; i < 16; ++i) {
                if (i == 4 || i == 6 || i == 8 || i == 10) oss << '-';
                oss << std::setw(2) << static_cast<unsigned int>(bytes[i]);
            }
            result["value"] = oss.str();
            break;
        }

        case proton::BINARY:
            result["value"] = binary_to_hex(proton::get<proton::binary>(val));
            break;

        case proton::STRING:
            result["value"] = proton::get<std::string>(val);
            break;

        case proton::SYMBOL:
            result["value"] = std::string(proton::get<proton::symbol>(val));
            break;

        default:
            result["value"] = "unknown";
            break;
    }

    return result;
}

// Infer AMQP type name from proton::value
std::string TypeCodec::infer_type(const proton::value& val) {
    switch (val.type()) {
        case proton::NULL_TYPE: return "null";
        case proton::BOOLEAN: return "boolean";
        case proton::UBYTE: return "ubyte";
        case proton::USHORT: return "ushort";
        case proton::UINT: return "uint";
        case proton::ULONG: return "ulong";
        case proton::BYTE: return "byte";
        case proton::SHORT: return "short";
        case proton::INT: return "int";
        case proton::LONG: return "long";
        case proton::FLOAT: return "float";
        case proton::DOUBLE: return "double";
        case proton::CHAR: return "char";
        case proton::TIMESTAMP: return "timestamp";
        case proton::UUID: return "uuid";
        case proton::BINARY: return "binary";
        case proton::STRING: return "string";
        case proton::SYMBOL: return "symbol";
        default: return "unknown";
    }
}

} // namespace qit
