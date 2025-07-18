import apiClient from "./axios";
import { getProductionOrders, type ProductionOrderData } from "./productionOrdersApi";
import { getScheduledTasks, type ScheduledTaskData } from "./scheduledTaskApi";
import { getDowntimeEvents, type DowntimeEventData } from "./downtimeEventsApi";
import { getMachines, type MachineData } from "./machinesAPI";

// Defining the shape of data the dahsboard will recieve
export interface DashboardData {
    productionOrders: ProductionOrderData[];
    scheduledTasks: ScheduledTaskData[];
    downtimeEvents: DowntimeEventData[];
    machines: MachineData[];
}

// Fetches all data required for main dashboard in parallel.
export const getDashboardData = async (): Promise<DashboardData> => {
    const [productionOrders, scheduledTasks, downtimeEvents, machines] = await Promise.all([
        getProductionOrders(),
        getScheduledTasks(),
        getDowntimeEvents(),
        getMachines(), 
    ]);

    return {
        productionOrders,
        scheduledTasks,
        downtimeEvents,
        machines,
    };
};