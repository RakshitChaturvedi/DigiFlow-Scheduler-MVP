import React, { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { getDashboardData, type DashboardData } from "../../api/dashboardApi";
import { Link } from "react-router-dom";
import GanttChart from "../../components/ganttChart";

interface KpiCardProps {
  title: string;
  value: string | number;
  colorClass: string;
}

const KpiCard: React.FC<KpiCardProps> = ({ title, value, colorClass }) => (
  <div className="bg-white p-6 rounded-lg shadow-sm">
    <h3 className="text-lg font-medium text-gray-600">{title}</h3>
    <p className={`text-4xl font-bold mt-2 ${colorClass}`}>{value}</p>
  </div>
);

const Dashboard: React.FC = () => {
  const { data, isLoading, isError, error } = useQuery<DashboardData, Error>({
    queryKey: ['dashboardData'],
    queryFn: getDashboardData,
    staleTime: 60*1000, // Refetch data every minute
    refetchInterval: 60*1000,
  });

  // --- KPI Calculations ---
  // useMemo to ensure complex calculations only run when data changes
  const kpiMetrics = useMemo(() => {
    if (!data) {
      return {
        utilization: 0,
        completedOrders: 0,
        activeAlerts: 0,
        jobsInProgress: 0,
        unscheduledOrders: [],
      };
    }
    
    const {productionOrders, scheduledTasks, downtimeEvents, machines} = data;

    // 1: Machine utilization
    const activeMachines = machines.filter(m => m.is_active);
    const machinesInProgress = new Set(
      scheduledTasks.filter(t => t.status.toLowerCase() === 'in_progress').map(t => t.assigned_machine.machine_id_code)
    ).size;
    const utilization = activeMachines.length > 0 ? Math.round((machinesInProgress / activeMachines.length) * 100) : 0;

    // 2: Completed Orders (Today)
    const todayString = new Date().toLocaleDateString('en-CA');

    const completedOrders = productionOrders.filter(o => {
        if (o.current_status.toLowerCase() !== 'completed' || !o.updated_at) {
            return false;
        }
        // Convert the order's UTC update time to a 'YYYY-MM-DD' string in the local timezone.
        const completedDateString = new Date(o.updated_at).toLocaleDateString('en-CA');
        // Now, compare the strings. This works correctly across timezones.
        return completedDateString === todayString;
    }).length;

    // 3: Active Downtime Alerts
    const activeAlerts = downtimeEvents.length;
    
    // 4: Jobs in Progress
    const jobsInProgress = scheduledTasks.filter(t => t.status.toLowerCase() === 'in_progress').length;

    // 5: Unscheduled Orders List
    const unscheduledOrders = productionOrders.filter(o => o.current_status.toLowerCase() === 'pending');

    return {utilization, completedOrders, activeAlerts, jobsInProgress, unscheduledOrders};
  }, [data]);

  if (isLoading) {
    return <div className="text-center p-8">Loading Dashboard Data...</div>;
  }

  if (isError) {
    return <div className="text-center p-8 text-red-600">Error loading dashboard: {error.message}</div>;
  }

  return (
    <div className="bg-backgroundLight overflow-auto">
      <h2 className="text-2xl font-bold text-textDark mb-6">Dashboard Overview</h2>

      {/* KPI Widgets */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <KpiCard title="Machine Utilization" value={`${kpiMetrics.utilization}%`} colorClass="text-primaryBlue" />
        <KpiCard title="Jobs In Progress" value={kpiMetrics.jobsInProgress} colorClass="text-orangeProgress" />
        <KpiCard title="Completed Today" value={kpiMetrics.completedOrders} colorClass="text-primaryGreen" />
        <KpiCard title="Active Downtime Alerts" value={kpiMetrics.activeAlerts} colorClass="text-redAlert" />
      </div>

      {/* Schedule Gnatt Chart Placeholder */}
      <div className="bg-white p-6 rounded-lg shadow-sm mb-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-xl font-semibold text-textDark">Live Schedule</h3>
          <Link to="/schedule" className="text-sm font-medium text-primaryBlue hover:underline">
            View Full Schedule &rarr;
          </Link>
        </div>
        <GanttChart />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Unscheduled Orders List */}
        <div className="bg-white p-6 rounded-lg shadow-sm">
          <h3 className="text-xl font-semibold text-textDark mb-4">Unscheduled Orders</h3>
          {kpiMetrics.unscheduledOrders.length > 0 ? (
            <ul className="space-y-2">
              {kpiMetrics.unscheduledOrders.slice(0,5).map(order => (
                <li key={order.id} className="text-gray-700 flex justify-between">
                  <span>{order.order_id_code} - {order.product_name}</span>
                  <span className="font-medium text-gray-500">Due: {new Date(order.due_date!).toLocaleDateString()}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-gray-500">No pending orders.</p>
          )}
        </div>

        {/* Active Alerts List */}
        <div className="bg-white p-6 rounded-lg shadow-sm">
          <h3 className="text-xl font-semibold text-textDark mb-4">Recent Downtime Events</h3>
          {data && data.downtimeEvents.length > 0 ? (
            <ul className="space-y-2">
              {data.downtimeEvents.slice(0,5).map(event => (
                <li key={event.id} className="text-redAlert flex justify-between">
                  <span>{event.machine?.machine_id_code || `Machine ID: ${event.machine_id}`}</span>
                  <span className="font-medium">{event.reason}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-gray-500">No active downtime events.</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;