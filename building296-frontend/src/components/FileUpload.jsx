import React, { useState } from "react";

const FileUpload = ({ setMessage }) => {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);

  const handleUpload = async () => {
    if (!file) {
      setMessage("Please select an Excel file first.");
      return;
    }

    setUploading(true);
    setMessage("");

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch(`${import.meta.env.VITE_API_URL}/import-excel`, {
        method: "POST",
        headers: {
          "X-API-Key": import.meta.env.VITE_API_KEY,
        },
        body: formData,
      });

      const data = await res.json();
      setMessage(`✅ ${data.status}: ${data.rows_imported} rows imported.`);
    } catch (err) {
      setMessage(`❌ Error: ${err.message}`);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="bg-white p-6 rounded-xl shadow-md mb-6">
      <h2 className="text-lg font-semibold mb-4">Upload Excel File</h2>
      <input
        type="file"
        accept=".xlsx"
        onChange={(e) => setFile(e.target.files[0])}
        className="border p-2 rounded-md"
      />
      <button
        onClick={handleUpload}
        disabled={uploading}
        className="ml-3 bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
      >
        {uploading ? "Uploading..." : "Upload"}
      </button>
    </div>
  );
};

export default FileUpload;
