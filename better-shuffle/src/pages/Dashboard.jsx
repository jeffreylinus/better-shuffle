import { useState, useEffect } from 'react';
import { API } from '../api';

function Dashboard() {
    const [playlists, setPlaylists] = useState([]);
    const [error, setError] = useState(null);

    useEffect(() => {
        async function fetchPlaylists() {
            try {
                const response = await fetch(`${API}/api/list-playlists`, {
                    credentials: 'include',
                });
                if (!response.ok) {
                    window.location.href = '/';
                    return;
                }
                const data = await response.json();
                setPlaylists(Array.isArray(data) ? data : []);
            } catch (err) {
                setError(err);
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
            {error && <p>{error.message || 'Something went wrong'}</p>}
            {playlists.map((playlist) => (
                <button
                    key={playlist.id}
                    onClick={async () => {
                        setError(null);
                        try {
                            const response = await fetch(
                                `${API}/api/playlists/${playlist.id}/shuffle`,
                                {
                                    method: 'POST',
                                    credentials: 'include',
                                },
                            );
                            if (!response.ok) {
                                const data = await response.json().catch(() => null);
                                const detail = data?.detail;
                                throw new Error(
                                    typeof detail === 'string'
                                        ? detail
                                        : 'Could not start playback',
                                );
                            }
                        } catch (err) {
                            setError(err);
                        }
                    }}
                >
                    {playlist.name}
                </button>
            ))}
        </div>
        </>
    );
}

export default Dashboard;
