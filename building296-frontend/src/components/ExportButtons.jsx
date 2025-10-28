const ExportButtons = () => {
  const handleDownload = (endpoint) => {
    window.open(`${import.meta.env.VITE_API_URL}/${endpoint}`, "_blank");
  };

  return (
    <div className="bg-white p-6 rounded-xl shadow-md mb-6 flex flex-col items-center">
      <h2 className="text-lg font-semibold mb-4">Exports</h2>
      <div className="space-x-4">
        <button
          onClick={() => handleDownload("export_month_report")}
          className="bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700"
        >
          Download Monthly Report
        </button>
        <button
          onClick={() => handleDownload("export_wallet_ledger")}
          className="bg-gray-700 text-white px-4 py-2 rounded-md hover:bg-gray-800"
        >
          Download Wallet Ledger
        </button>
      </div>
    </div>
  );
};

export default ExportButtons;
