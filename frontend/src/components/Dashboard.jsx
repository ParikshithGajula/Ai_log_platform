import React from 'react';

function Dashboard() {
  return (
    <div className="bg-[#1a232e] rounded-lg p-6">
      <h2 className="text-2xl font-bold mb-4">Dashboard</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-[#161b22] p-4 rounded">
          <h3 className="text-lg font-semibold mb-2">Total Files</h3>
          <p className="text-3xl font-bold">124</p>
        </div>
        <div className="bg-[#161b22] p-4 rounded">
          <h3 className="text-lg font-semibold mb-2">Successful Uploads</h3>
          <p className="text-3xl font-bold">98</p>
        </div>
        <div className="bg-[#161b22] p-4 rounded">
          <h3 className="text-lg font-semibold mb-2">Failed Uploads</h3>
          <p className="text-3xl font-bold">26</p>
        </div>
        <div className="bg-[#161b22] p-4 rounded">
          <h3 className="text-lg font-semibold mb-2">Last Upload</h3>
          <p className="text-3xl font-bold">2023-10-15</p>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
