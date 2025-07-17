import React from "react";

const Dashboard: React.FC = () => {
  return (
    <div className="bg-backgroundLight overflow-auto">
      <h2 className="text-2xl font-bold text-textDark mb-6">Dashboard Overview</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {/* KPI Widgets */}

        <div className="bg-white p-6 rounded-lg shadow-sm">
          <h3 className="text-lg font-medium text-gray-600">Machine Utilization %</h3>
          <p className="text-4xl font-bold text-primaryBlue mt-2">75%</p>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm">
          <h3 className="text-lg font-medium text-gray-600">Jobs On-Time %</h3>
          <p className="text-4xl font-bold text-primaryGreen mt-2">92%</p>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm">
          <h3 className="text-lg font-medium text-gray-600">Active Downtime Alerts</h3>
          <p className="text-4xl font-bold text-redAlert mt-2">3</p>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm">
          <h3 className="text-lg font-medium text-gray-600">OEE %</h3>
          <p className="text-4xl font-bold text-orangeProgress mt-2">85%</p>
        </div>
      </div>

      {/* Schedule Gantt Chart Placeholder */}
      <div className="bg-white p-6 rounded-lg shadow-sm mb-6">
        <h3 className="text-xl font-semibold text-textDark mb-4">Schedule Gantt Chart</h3>
        <div className="h-96 bg-gray-100 flex items-center justify-center text-gray-500 rounded-md border border-dashed border-borderColor">
          [Interavtive Gnatt Chart will go here]
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Unscheduled orders placeholder */}
        <div className="bg-white p-6 rounded-lg shadow-sm">
          <h3 className="text-xl font-semibold text-textDark mb-4">Unscheduled Orders</h3>
          <ul className="list-disc pl-5 text-gray-700">
            <li>Order #ORD-001 - Due: 2025-07-10</li>
            <li>Order #ORD-005 - Due: 2025-07-12</li>
            <li>Order #ORD-0010 - Due: 2025-07-15</li>
          </ul>
        </div>

        {/* Active Alerts Placeholder */}
        <div className="bg-white p-6 rounded-lg shadow-sm">
          <h3 className="text-xl font-semibold text-textDark mb-4">Active Alerts</h3>
          <ul className="list-disc pl-5 text-redAlert">
            <li>Machine Lathe-01: Spindle issue (Since 10:00AM) </li>
            <li>Machine Mill-03: Power outage (Since 11:30 AM)</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;