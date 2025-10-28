const MessageBox = ({ message }) => {
  if (!message) return null;
  return (
    <div className="bg-white p-4 rounded-md shadow text-center text-gray-700 w-96">
      {message}
    </div>
  );
};

export default MessageBox;
