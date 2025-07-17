import React from "react";
import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { getMachines, type MachineData } from "../../api/machinesAPI";
import { useAuth } from "../../auth/AuthContext";

const MachineSelectPage: React.FC = () => {
    const navigate = useNavigate();
    const { logout } = useAuth();

    // fetches all machines
    const { data: machines, isLoading, isError } = useQuery<MachineData[], Error>({
        queryKey: ['allMachinesForOperator'], // using a unique key for query
        queryFn: getMachines,
        staleTime: 5*60*1000, // cache for 5 minutes 
    });

    const handleMachineSelect = (machineIdCode: string) => {
        navigate(`/operator/task/${machineIdCode}`);
    };

    return (
        <div className="bg-gray-900 text-white min-h-screen p-4 sm:p-8">
            <header className="flex justify-between items-center mb-12 border-b border-gray-700 pb-4">
                <h1 className="text-3xl sm:text-4xl font-bold">Select Machine</h1>
                <button
                    onClick={logout}
                    className="bg-red-600 text-white px-4 py-2 rounded-lg font-semibold hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 focus:ring-offset-gray-900 transition-colors"
                >
                    Logout
                </button>
            </header>

            <main>
                {isLoading && (
                    <div className="text-center text-gray-400 text-2xl animate-pulse">Loading Machines...</div>
                )}
                {isError && (
                    <div className="text-center text-red-400 text-2xl">Error: Could not load machine list. Please try again.</div>
                )}
                {!isLoading && !isError && (
                    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4 sm:gap-6">
                        {machines && machines.filter(m => m.is_active).map((machine) => (
                            <button
                                key={machine.id}
                                onClick={() => handleMachineSelect(machine.machine_id_code)}
                                className="aspect-square bg-gray-800 rounded-lg shadow-lg text-white flex flex-col items-center justify-center p-2 text-center hover:bg-blue-600 hover:scale-105 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-gray-900 transition-all duration-200 ease-in-out"
                            >
                                <span className="text-5xl mb-2" role="img" aria-label="gear">⚙️</span>
                                <span className="text-lg sm:text-xl font-bold break-words">{machine.machine_id_code}</span>
                                <span className="text-sm text-gray-400">{machine.machine_type}</span>
                            </button>
                        ))}
                    </div>
                )}
                { !isLoading && !isError && machines && machines.filter(m => m.is_active).length===0 &&(
                    <div className="text-center text-gray-500 text-2xl">No active machines found in the catalog.</div>
                )}
            </main>
        </div>
    );
};

export default MachineSelectPage;

