import { createContext, useContext, useEffect, useState } from "react";

const ChatContext = createContext();

export const ChatProvider = ({ children }) => {
  const chat = async (message) => {
    setLoading(true);
    try {
      // Use "/chat" for the Vite proxy (recommended in development)
      const data = await fetch("/chat", { 
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ message }),
      });

      if (!data.ok) {
        throw new Error(`HTTP error! status: ${data.status}`);
      }

      const resp = (await data.json()).messages;
      setMessages((messages) => [...messages, ...resp]);
    } catch (error) {
      console.error("Error during chat:", error);
      // Optionally, display an error message to the user
    } finally {
      setLoading(false);
    }
  };

  const [messages, setMessages] = useState([]);
  const [message, setMessage] = useState();
  const [loading, setLoading] = useState(false);
  const [cameraZoomed, setCameraZoomed] = useState(true);
  const onMessagePlayed = () => {
    setMessages((messages) => messages.slice(1));
  };

  useEffect(() => {
    if (messages.length > 0) {
      setMessage(messages[0]);
    } else {
      setMessage(null);
    }
  }, [messages]);

  return (
    <ChatContext.Provider
      value={{
        chat,
        message,
        onMessagePlayed,
        loading,
        cameraZoomed,
        setCameraZoomed,
      }}
    >
      {children}
    </ChatContext.Provider>
  );
};

export const useChat = () => {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error("useChat must be used within a ChatProvider");
  }
  return context;
};