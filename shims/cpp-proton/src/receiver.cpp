/*
 * QIT C++ Proton Shim - Receiver Implementation
 */

#include "qit_shim.hpp"
#include <json/json.h>
#include <proton/delivery.hpp>
#include <proton/transport.hpp>
#include <proton/work_queue.hpp>
#include <iostream>
#include <cstdlib>

namespace qit {

Receiver::Receiver(const std::string& broker_url,
                   const std::string& queue_name,
                   size_t count,
                   int timeout_sec)
    : broker_url_(broker_url),
      queue_name_(queue_name),
      expected_count_(count),
      received_count_(0),
      timeout_sec_(timeout_sec),
      output_sent_(false) {}

void Receiver::on_container_start(proton::container& c) {
    c.open_receiver(broker_url_ + "/" + queue_name_);

    // Set timeout using std::function wrapped work
    if (timeout_sec_ > 0) {
        proton::work timeout_work = proton::make_work([this]() {
            this->on_timeout();
        });
        c.schedule(proton::duration(timeout_sec_ * 1000), timeout_work);
    }
}

void Receiver::on_message(proton::delivery& d, proton::message& m) {
    try {
        Json::Value decoded = TypeCodec::decode(m.body());

        Json::Value msg_data;
        msg_data["index"] = static_cast<int>(received_count_);
        msg_data["type"] = decoded["type"];
        msg_data["value"] = decoded["value"];

        received_messages_.append(msg_data);
        received_count_++;

        if (received_count_ >= expected_count_) {
            d.receiver().close();
            d.connection().close();

            // Output result
            output_result();
        }
    } catch (const std::exception& e) {
        std::cerr << "Error processing message: " << e.what() << std::endl;
        d.receiver().close();
        d.connection().close();
        throw;
    }
}

void Receiver::on_timeout() {
    // Output what we received so far
    output_result();

    if (received_count_ < expected_count_) {
        std::exit(1);  // Exit with error if we didn't get all messages
    }
}

void Receiver::output_result() {
    if (output_sent_) return;  // Already output, don't duplicate
    output_sent_ = true;

    Json::Value result;
    result["messages"] = received_messages_;
    result["stats"]["received"] = static_cast<Json::Value::UInt>(received_count_);

    Json::StreamWriterBuilder builder;
    builder["indentation"] = "  ";
    std::cout << Json::writeString(builder, result) << std::endl;
}

void Receiver::on_transport_error(proton::transport& t) {
    std::cerr << "Transport error: " << t.error() << std::endl;
}

void Receiver::on_error(const proton::error_condition& ec) {
    std::cerr << "Error: " << ec << std::endl;
}

} // namespace qit
