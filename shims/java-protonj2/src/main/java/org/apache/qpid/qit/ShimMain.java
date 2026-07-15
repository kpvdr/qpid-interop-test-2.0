/*
 * QIT ProtonJ2 Shim - Main Entry Point
 */
package org.apache.qpid.qit;

public class ShimMain {
    public static void main(String[] args) {
        if (args.length < 1) {
            System.err.println("Usage: shim <command> [options]");
            System.err.println("Commands: send, receive");
            System.exit(1);
        }

        String command = args[0];
        
        try {
            switch (command) {
                case "send":
                    Sender.main(args);
                    break;
                case "receive":
                    Receiver.main(args);
                    break;
                default:
                    System.err.println("Unknown command: " + command);
                    System.exit(1);
            }
        } catch (Exception e) {
            System.err.println("Error: " + e.getMessage());
            e.printStackTrace(System.err);
            System.exit(1);
        }
    }
}
