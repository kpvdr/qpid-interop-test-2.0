/*
 * QIT .NET Apache Qpid Proton Shim - Sender
 */

using System;
using System.Collections.Generic;
using Apache.Qpid.Proton.Client;
using Newtonsoft.Json;

namespace Qit.Shim
{
    public static class Sender
    {
        public static void Send(string broker, string queue, string type, string data)
        {
            try
            {
                var testData = JsonConvert.DeserializeObject<List<TestMessage>>(data);
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
                using ISender sender = connection.OpenSender(queue);

                // Send all messages
                foreach (var testMsg in testData)
                {
                    var message = IMessage<object>.Create();
                    message.MessageId = testMsg.Index.ToString();
                    message.Body = TypeCodec.Encode(type, testMsg.Value);

                    sender.Send(message);

                    messages.Add(new MessageResult
                    {
                        Index = testMsg.Index,
                        Type = type,
                        Value = testMsg.Value
                    });
                }

                // Output result
                var result = new
                {
                    messages,
                    stats = new { sent = messages.Count }
                };

                Console.WriteLine(JsonConvert.SerializeObject(result, Formatting.Indented));
            }
            catch (Exception ex)
            {
                Console.Error.WriteLine($"Send error: {ex.Message}");
                Environment.Exit(1);
            }
        }

        private static (string Host, int Port) ParseBrokerUrl(string broker)
        {
            var uri = new Uri(broker.StartsWith("amqp://") ? broker : $"amqp://{broker}");
            return (uri.Host, uri.Port > 0 ? uri.Port : 5672);
        }
    }

    public class TestMessage
    {
        [JsonProperty("index")]
        public int Index { get; set; }

        [JsonProperty("value")]
        public object Value { get; set; }
    }

    public class MessageResult
    {
        [JsonProperty("index")]
        public int Index { get; set; }

        [JsonProperty("type")]
        public string Type { get; set; }

        [JsonProperty("value")]
        public object Value { get; set; }
    }
}
