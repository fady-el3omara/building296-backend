import React, { useState } from "react";
import FileUpload from "./components/FileUpload";
import ExportButtons from "./components/ExportButtons";
import MessageBox from "./components/MessageBox";

function App() {
  const [message, setMessage] = useState("");

  return (
    <div className="min-h-screen bg-gray-100 flex flex-col items-center py-12">
      <h1 className="text-3xl font-bold mb-8 text-gray-800">
        🏢 Building 296 Admin Dashboard
      </h1>

      <FileUpload setMessage={setMessage} />
      <ExportButtons />
      <MessageBox message={message} />
    </div>
  );
}

export default App;
