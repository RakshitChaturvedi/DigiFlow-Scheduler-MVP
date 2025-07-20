import React from 'react';
import { useQuery } from '@tanstack/react-query';
import apiClient from '../api/axios';
import Plot from 'react-plotly.js';

// Api function to fetch the chart data
const getGanttChartData = async (): Promise<any> => {
    const response = await apiClient.get('/api/schedule/gantt');
    return JSON.parse(response.data)
};

const GanttChart: React.FC = () => {
    const { data: figure, isLoading, isError, error } = useQuery({
        queryKey: ['ganttChartData'],
        queryFn: getGanttChartData,
        staleTime: 5 * 60 * 1000, // Cache for 5 minutes
    });

    if (isLoading) {
        return (
            <div className='h-96 flex items-center justify-center text-gray-500'>
                Generating Gantt Chart...
            </div>
        );
    }

    if (isError) {
        return (
            <div className='h-96 flex items-center justify-center text-red-500'>
                Error loading chart: {(error as Error).message}
            </div>
        );
    }

    return (
        <Plot 
            data={figure.data}
            layout={figure.layout}
            useResizeHandler={true}
            style={{ width: '100%', height: '100%' }}
            config={{ responsive: true, displaylogo: false }}
        />
    );
};

export default GanttChart;