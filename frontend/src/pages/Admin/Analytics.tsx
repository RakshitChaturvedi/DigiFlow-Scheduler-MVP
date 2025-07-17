import React from 'react';

interface AnalyticsProps {

}

const Analytics: React.FC<AnalyticsProps> = () => {
    return (
        <div className='bg-backgroundLight overflow-auto'>
            <h2 className='text-2xl font-bold text-textDark mb-6'>Analytics</h2>

            {/* Date Range Picker Selection */}
            <div className='bg-white p-6 rounded-lg shadow-sm mb-6 flex flex-col md:flex-row md:items-center md:justify-between'>
                <h3 className='text-xl font-semibold text-textDark mb-4 md:mb-0'>View Stats For:</h3>
                <div className='flex flex-wrap gap-3'>
                    <button className='px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors duration-200 text-sm font-medium'>
                        Last 7 Days
                    </button>
                    <button className='px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors duration-200 text-sm font-medium'>
                        Last 30 Days
                    </button>
                    <button className='px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors duration-200 text-sm font-medium'>
                        Custom Range
                    </button>
                    <input type='date' className='px-4 py-2 border-borderColor rounded-lg text-gray-700 focus:ring-primaryBlue focus:border-primaryBlue transition-all duration-200 text-sm' />                                                    
                </div>
            </div>

            {/* Chart Widgets Grid (2x2 Grid) */}
            <div className='grid grid-cols-1 md:grid-cols-2 gap-6'>
                {/* Chart 1: OEE / utilization Over Time (Line Chart) */}
                <div className="bg-white p-6 rounded-lg shadow-sm min-h-[300px] flex items-center justify-center text-gray-500 border border-dashed border-borderColor">
                    <h3 className='text-xl font-semibold text-textDark mb-4 absolute top-6 left-6'>OEE / Utilization Over Time</h3>
                    <div className='text-center'>
                        [Line Chart Placeholder] {/* Integrate a charting library like recharts or chart.js */}
                    </div>
                </div>

                {/* Chart 2: On-Time vs. Late Orders (Bar Chart or Pie Chart) */}
                <div className="bg-white p-6 rounded-lg shadow-sm min-h-[300px] flex items-center justify-center text-gray-500 border border-dashed border-borderColor">
                    <h3 className="text-xl font-semibold text-textDark mb-4 absolute top-6 left-6">On-Time vs. Late Orders</h3>
                    <div className="text-center">
                        [Bar/Pie Chart Placeholder]
                    </div>
                </div>

                {/* Chart 3: Downtime by Reason (Pie Chart) */}
                <div className="bg-white p-6 rounded-lg shadow-sm min-h-[300px] flex items-center justify-center text-gray-500 border border-dashed border-borderColor">
                    <h3 className="text-xl font-semibold text-textDark mb-4 absolute top-6 left-6">Downtime by Reason</h3>
                    <div className="text-center">
                        [Pie Chart Placeholder]
                    </div>
                </div>

                {/* Chart 4: Job Turnaround Time by Process (Bar Chart) */}
                <div className="bg-white p-6 rounded-lg shadow-sm min-h-[300px] flex items-center justify-center text-gray-500 border border-dashed border-borderColor">
                    <h3 className="text-xl font-semibold text-textDark mb-4 absolute top-6 left-6">Job Turnaround Time by Process</h3>
                    <div className="text-center">
                        [Bar Chart Placeholder]
                    </div>
                </div>                
            </div>
        </div>
    );
};

export default Analytics
