/*
 * QIT C++ Proton Shim - Sender Implementation
 */

#include "qit_shim.hpp"
#include <json/json.h>
#include <proton/message_id.hpp>
#include <proton/transport.hpp>
#include <proton/annotation_key.hpp>
#include <proton/symbol.hpp>
#include <sstream>
#include <iomanip>
#include <iostream>
#include <map>

namespace qit {

Sender::Sender(const std::string& broker_url,
               const std::string& queue_name,
               const std::string& amqp_type,
               const std::string& test_data_json,
               bool jms_mode)
    : broker_url_(broker_url),
      queue_name_(queue_name),
      amqp_type_(amqp_type),
      sent_count_(0),
      confirmed_count_(0),
      jms_mode_(jms_mode) {

    // Parse JSON test data
    Json::CharReaderBuilder builder;
    Json::Value root;
    std::istringstream iss(test_data_json);
    std::string errors;

    if (!Json::parseFromStream(builder, iss, &root, &errors)) {
        throw std::runtime_error("Failed to parse JSON test data: " + errors);
    }

    if (!root.isArray()) {
        throw std::runtime_error("Test data must be a JSON array");
    }

    test_values_ = root;
}

int8_t Sender::get_jms_message_type(const std::string& amqp_type) const {
    // JMS message type constants (from Qpid JMS Client)
    const int8_t JMS_MESSAGE = 0;        // Empty message
    const int8_t JMS_TEXT_MESSAGE = 5;   // String/text
    const int8_t JMS_BYTES_MESSAGE = 3;  // Binary data

    // Map AMQP types to JMS message types
    if (amqp_type == "string") {
        return JMS_TEXT_MESSAGE;
    } else if (amqp_type == "binary") {
        return JMS_BYTES_MESSAGE;
    } else if (amqp_type == "null") {
        return JMS_MESSAGE;
    }

    // Other AMQP types not directly mapped to JMS
    return -1;  // Invalid
}

void Sender::on_container_start(proton::container& c) {
    c.open_sender(broker_url_ + "/" + queue_name_);
}

void Sender::on_sendable(proton::sender& s) {
    while (s.credit() && sent_count_ < test_values_.size()) {
        proton::message msg;
        const Json::Value& test_value = test_values_[static_cast<int>(sent_count_)];

        msg.id(proton::message_id(test_value["index"].asInt()));
        msg.body(TypeCodec::encode(amqp_type_, test_value["value"]));

        // Add JMS annotations if in JMS mode
        if (jms_mode_) {
            int8_t jms_type = get_jms_message_type(amqp_type_);
            if (jms_type >= 0) {
                // NOTE: Key MUST be symbol, value MUST be byte (not ubyte)
                // This matches Qpid JMS Client wire format
                proton::annotation_key jms_key(proton::symbol("x-opt-jms-msg-type"));
                msg.message_annotations().put(jms_key, jms_type);
            }
        }

        s.send(msg);
        sent_count_++;
    }
}

void Sender::on_tracker_accept(proton::tracker& t) {
    confirmed_count_++;

    if (confirmed_count_ == test_values_.size()) {
        // Output result as JSON
        Json::Value result;
        result["messages"] = test_values_;
        result["stats"]["sent"] = static_cast<Json::Value::UInt>(sent_count_);

        Json::StreamWriterBuilder builder;
        builder["indentation"] = "  ";
        std::cout << Json::writeString(builder, result) << std::endl;

        t.sender().close();
        t.connection().close();
    }
}

void Sender::on_transport_error(proton::transport& t) {
    std::cerr << "Transport error: " << t.error() << std::endl;
}

void Sender::on_error(const proton::error_condition& ec) {
    std::cerr << "Error: " << ec << std::endl;
}

} // namespace qit
