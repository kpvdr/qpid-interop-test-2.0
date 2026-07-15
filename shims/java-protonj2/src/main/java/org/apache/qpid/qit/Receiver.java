/*
 * QIT ProtonJ2 Shim - Receiver
 */
package org.apache.qpid.qit;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import org.apache.qpid.protonj2.client.Client;
import org.apache.qpid.protonj2.client.Connection;
import org.apache.qpid.protonj2.client.ConnectionOptions;
import org.apache.qpid.protonj2.client.Delivery;
import org.apache.qpid.protonj2.client.Message;

import java.net.URI;
import java.util.ArrayList;
import java.util.List;

public class Receiver {
    public static void main(String[] args) throws Exception {
        // Parse command-line arguments
        String broker = null;
        String queue = null;
        int count = 0;
        int timeout = 30;

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
                case "count":
                    count = Integer.parseInt(value);
                    break;
                case "timeout":
                    timeout = Integer.parseInt(value);
                    break;
            }
        }

        if (broker == null || queue == null || count == 0) {
            System.err.println("Missing required arguments");
            System.exit(1);
        }

        // Parse broker URL
        URI brokerUri = parseBrokerUrl(broker);

        // Create client and connect
        Client client = Client.create();
        ConnectionOptions options = new ConnectionOptions();
        options.user("artemis");
        options.password("artemis");

        try (Connection connection = client.connect(brokerUri.getHost(), brokerUri.getPort(), options);
             org.apache.qpid.protonj2.client.Receiver receiver = connection.openReceiver(queue)) {

            List<JsonObject> messages = new ArrayList<>();

            // Receive messages
            for (int i = 0; i < count; i++) {
                Delivery delivery = receiver.receive(timeout, java.util.concurrent.TimeUnit.SECONDS);
                
                if (delivery == null) {
                    break;  // Timeout
                }

                Message<?> message = delivery.message();
                TypeCodec.DecodedMessage decoded = TypeCodec.decode(message.body());

                JsonObject msgResult = new JsonObject();
                msgResult.addProperty("index", i);
                msgResult.addProperty("type", decoded.type);
                msgResult.add("value", decoded.value);
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
            stats.addProperty("received", messages.size());
            result.add("stats", stats);

            Gson prettyGson = new GsonBuilder()
                .setPrettyPrinting()
                .serializeNulls()  // Force serialization of null values
                .create();
            System.out.println(prettyGson.toJson(result));

            if (messages.size() < count) {
                System.exit(1);
            }
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
