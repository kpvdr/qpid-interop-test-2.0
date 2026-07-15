/*
 * QIT .NET Apache Qpid Proton Shim - Receiver
 */

using System;
using System.Collections.Generic;
using Apache.Qpid.Proton.Client;
using Newtonsoft.Json;

namespace Qit.Shim
{
    public static class Receiver
    {
        public static void Receive(string broker, string queue, int count, int timeout)
        {
            try
            {
                var messages = new List<MessageResult>();

                // Parse broker URL
                var brokerUri = ParseBrokerUrl(broker);

                // Create client and connect
                IClient client = IClient.Create();

                ConnectionOptions options = new ConnectionOptions
                {
                    User = "artemis",
                    Password = "artemis"
                };

                using IConnection connection = client.Connect(brokerUri.Host, brokerUri.Port, options);
                using IReceiver receiver = connection.OpenReceiver(queue);

                // Receive messages with timeout
                var timeoutMs = timeout * 1000;
                for (int i = 0; i < count; i++)
                {
                    IDelivery delivery = receiver.Receive(TimeSpan.FromMilliseconds(timeoutMs));

                    if (delivery == null)
                    {
                        break;  // Timeout
                    }

                    IMessage<object> message = delivery.Message();
                    var decoded = TypeCodec.Decode(message.Body);

                    messages.Add(new MessageResult
                    {
                        Index = i,
                        Type = decoded.Type,
                        Value = decoded.Value
                    });
                }

                // Output result
                var result = new
                {
                    messages,
                    stats = new { received = messages.Count }
                };

                Console.WriteLine(JsonConvert.SerializeObject(result, Formatting.Indented));

                if (messages.Count < count)
                {
                    Environment.Exit(1);
                }
            }
            catch (Exception ex)
            {
                Console.Error.WriteLine($"Receive error: {ex.Message}");
                Environment.Exit(1);
            }
        }

        private static (string Host, int Port) ParseBrokerUrl(string broker)
        {
            var uri = new Uri(broker.StartsWith("amqp://") ? broker : $"amqp://{broker}");
            return (uri.Host, uri.Port > 0 ? uri.Port : 5672);
        }
    }
}
