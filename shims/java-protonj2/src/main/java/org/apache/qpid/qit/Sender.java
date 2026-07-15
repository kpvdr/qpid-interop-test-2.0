/*
 * QIT ProtonJ2 Shim - Sender
 */
package org.apache.qpid.qit;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import org.apache.qpid.protonj2.client.Client;
import org.apache.qpid.protonj2.client.Connection;
import org.apache.qpid.protonj2.client.ConnectionOptions;
import org.apache.qpid.protonj2.client.Message;

import java.net.URI;
import java.util.ArrayList;
import java.util.List;

public class Sender {
    public static void main(String[] args) throws Exception {
        // Parse command-line arguments
        String broker = null;
        String queue = null;
        String type = null;
        String data = null;

        for (int i = 1; i < args.length; i += 2) {
            String key = args[i].replace("--", "");
            String value = args[i + 1];

            switch (key) {
                case "broker":
                    broker = value;
                    break;
                case "queue":
                    queue = value;
                    break;
                case "type":
                    type = value;
                    break;
                case "data":
                    data = value;
                    break;
            }
        }

        if (broker == null || queue == null || type == null || data == null) {
            System.err.println("Missing required arguments");
            System.exit(1);
        }

        // Parse broker URL
        URI brokerUri = parseBrokerUrl(broker);

        // Parse test data
        Gson gson = new Gson();
        JsonArray testData = gson.fromJson(data, JsonArray.class);

        // Create client and connect
        Client client = Client.create();
        ConnectionOptions options = new ConnectionOptions();
        options.user("artemis");
        options.password("artemis");

        try (Connection connection = client.connect(brokerUri.getHost(), brokerUri.getPort(), options);
             org.apache.qpid.protonj2.client.Sender sender = connection.openSender(queue)) {

            List<JsonObject> messages = new ArrayList<>();

            // Send all messages
            for (int i = 0; i < testData.size(); i++) {
                JsonObject testMsg = testData.get(i).getAsJsonObject();
                int index = testMsg.get("index").getAsInt();
                Object value = testMsg.get("value");

                Message<Object> message = Message.create();
                message.messageId(String.valueOf(index));
                message.body(TypeCodec.encode(type, value));

                sender.send(message);

                // Record sent message
                JsonObject msgResult = new JsonObject();
                msgResult.addProperty("index", index);
                msgResult.addProperty("type", type);

                // Explicitly handle null values - must include "value" key even when null
                JsonElement valueElement = testMsg.get("value");
                if (valueElement == null || valueElement.isJsonNull()) {
                    msgResult.add("value", com.google.gson.JsonNull.INSTANCE);
                } else {
                    msgResult.add("value", valueElement);
                }
                messages.add(msgResult);
            }

            // Output result
            JsonObject result = new JsonObject();
            JsonArray messagesArray = new JsonArray();
            for (JsonObject msg : messages) {
                messagesArray.add(msg);
            }
            result.add("messages", messagesArray);

            JsonObject stats = new JsonObject();
            stats.addProperty("sent", messages.size());
            result.add("stats", stats);

            Gson prettyGson = new GsonBuilder()
                .setPrettyPrinting()
                .serializeNulls()  // Force serialization of null values
                .create();
            System.out.println(prettyGson.toJson(result));
        }
    }

    private static URI parseBrokerUrl(String broker) throws Exception {
        if (!broker.startsWith("amqp://")) {
            broker = "amqp://" + broker;
        }
        URI uri = new URI(broker);
        return uri;
    }
}
