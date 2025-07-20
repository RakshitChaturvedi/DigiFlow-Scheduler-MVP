import React from "react";
import { useQuery } from "@tanstack/react-query";
import { PieChart, Pie, Cell, Tooltip, Legend, BarChart, Bar, XAxis, YAxis, CartesianGrid, ResponsiveContainer } from 'recharts';
import { getAnalyticsData, type AnalyticsData } from "../../api/analyticsApi";

// Reusable card component to hold our charts
const ChartCard = ({ title, children }: {title: string, children: React.ReactNode}) => (
    <div className="bg-white p-6 rounded-lg shadow-sm">
        <h3 className="text-xl font-semibold text-textDark mb-4">{title}</h3>
        <div style={{width: '100%', height: 300}}>
            {children}
        </div>
    </div>
);

const AnalyticsPage: React.FC = () => {
    const { data, isLoading, isError, error } = useQuery<AnalyticsData, Error>({
        queryKey: ['analyticsData'],
        queryFn: getAnalyticsData,
    });

    if (isLoading) return <div className="text-center p-8">Loading analytics...</div>;
    if (isError) return <div className="text-center p-8 text-red-600">Error loading analytics: {error.message}</div>

    const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#AF19FF'];

    return (
        <div className="bg-backgroundLight overflow-auto">
            <h2 className="text-2xl font-bold text-textDark mb-6">Analytics</h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <ChartCard title="Downtime by Reason">
                    <ResponsiveContainer>
                        <PieChart>
                            <Pie
                                data={data?.downtime_by_reason}
                                cx="50%"
                                cy="50%"
                                labelLine={false}
                                outerRadius={80}
                                fill="#8884d8"
                                dataKey="count"
                                nameKey="reason"
                                label={({ name, percent }) => `${name} ${(percent*100).toFixed(0)}%`}
                            >
                                {data?.downtime_by_reason.map((entry, index) => (
                                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                ))}
                            </Pie>
                            <Tooltip />
                            <Legend />        
                        </PieChart>
                    </ResponsiveContainer>
                </ChartCard>

                <ChartCard title="Order Status Summary">
                <ResponsiveContainer>
                    <BarChart data={data?.order_status_summary} margin={{ top: 5, right: 20, left: -10, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="status" />
                    <YAxis allowDecimals={false} />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="count" fill="#8884d8" name="Number of Orders" />
                    </BarChart>
                </ResponsiveContainer>
                </ChartCard>
                
                {/* Placeholder for future charts */}
                <div className="bg-white p-6 rounded-lg shadow-sm min-h-[300px] flex items-center justify-center text-gray-500 border border-dashed border-borderColor">
                    [Future Chart Placeholder]
                </div>
                <div className="bg-white p-6 rounded-lg shadow-sm min-h-[300px] flex items-center justify-center text-gray-500 border border-dashed border-borderColor">
                    [Future Chart Placeholder]
                </div>
            </div>
        </div>
    );
};

export default AnalyticsPage;