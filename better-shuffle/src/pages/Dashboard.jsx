import { useState, useEffect } from 'react';

function Dashboard() {
    const [playlists, setPlaylists] = useState([]);
    const [error, setError] = useState(null);

    useEffect(() => {
        async function fetchPlaylists() {
            try {
                const response = await fetch('/api/list-playlists');
                const data = await response.json();
                setPlaylists(data);
            } catch (error) {
                setError(error);
            }
        }
        fetchPlaylists();
    }, []);

    return (
        <>
        <div>
            <h1>Dashboard</h1>
        </div>

        <div>
            <h2>Playlists</h2>
            {playlists.map((playlist) => (
                <button > playlist.name  </button>
            
        
        
        ))}

        </div>
        </>
    )
}

export default Dashboard;