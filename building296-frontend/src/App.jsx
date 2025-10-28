import React, { useEffect, useState } from "react";
import { fetchOwnersDistribution } from "./api";

function App() {
  const [owners, setOwners] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fetch data from backend when the component loads
  useEffect(() => {
    async function loadData() {
      try {
        const data = await fetchOwnersDistribution();
        setOwners(data);
      } catch (err) {
        setError("Failed to load data from backend.");
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center py-10">
      <h1 className="text-3xl font-bold text-gray-800 mb-6">
        🏢 Building 296 — Owner Distribution
      </h1>

      {loading && <p className="text-gray-500">Loading data...</p>}
      {error && <p className="text-red-500">{error}</p>}

      {!loading && !error && (
        <div className="overflow-x-auto w-11/12 md:w-3/4 bg-white rounded-xl shadow-md p-4">
          <table className="min-w-full text-left border-collapse">
            <thead>
              <tr className="border-b bg-gray-100">
                <th className="p-3 font-semibold text-gray-700">Owner</th>
                <th className="p-3 font-semibold text-gray-700">Expected Net</th>
                <th className="p-3 font-semibold text-gray-700">Share Held</th>
              </tr>
            </thead>
            <tbody>
              {owners.map((o) => (
                <tr key={o.ownerId} className="border-b hover:bg-gray-50">
                  <td className="p-3">{o.name}</td>
                  <td className="p-3">{o.expectedNet?.toLocaleString() || "-"}</td>
                  <td className="p-3">{o.shareHeld || "-"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default App;
