import { API } from '../api';

function Login() {
    return (
        <button
            onClick={() => {
                window.location.href = `${API}/api/auth`;
            }}
        >
            Connect to Spotify
        </button>
    );
}

export default Login;
