import React, { useState, useEffect, useRef } from 'react';
import { ChevronRight, Wind, Sunset, Sunrise, Droplets, Thermometer, AlertTriangle, Map as MapIcon, User, SlidersHorizontal, Sun, LineChart, Search, Camera } from 'lucide-react';
import styles from './AqiScreen.module.css';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import { Line } from 'react-chartjs-2';
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler } from 'chart.js';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler);


const LoginSignUpPage = ({ onLogin }) => {
  const [isSignUpActive, setIsSignUpActive] = useState(false);
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [age, setAge] = useState('');
  const [password, setPassword] = useState('');
  const [loginEmail, setLoginEmail] = useState('');
  const [loginPassword, setLoginPassword] = useState('');

  const handleSignUp = (e) => {
    e.preventDefault();
    if (!name || !email || !password || !age) { alert("Please fill in all fields."); return; }
    const user = { name, email, age, password };
    localStorage.setItem('weatherAppUser', JSON.stringify(user));
    alert("Sign up successful! Please sign in.");
    setIsSignUpActive(false);
  };

  const handleLogin = (e) => {
    e.preventDefault();
    try {
      const storedUser = JSON.parse(localStorage.getItem('weatherAppUser'));
      if (!storedUser) { alert("No user found. Please sign up first."); return; }
      if (storedUser.email.trim() === loginEmail.trim() && storedUser.password.trim() === loginPassword.trim()) {
        onLogin(storedUser);
      } else {
        alert("Invalid email or password.");
      }
    } catch (error) { alert("Could not log in. Please sign up first."); }
  };

  return (
    <div className={styles.loginContainerWrapper}>
      <div className={`${styles.loginContainer} ${isSignUpActive ? styles.rightPanelActive : ''}`}>
        <div className={`${styles.formContainer} ${styles.signUpContainer}`}>
          <form onSubmit={handleSignUp}>
            <h1>Create Account</h1>
            <input type="text" placeholder="Name" value={name} onChange={(e) => setName(e.target.value)} required />
            <input type="email" placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} required />
            <input type="number" placeholder="Age" value={age} onChange={(e) => setAge(e.target.value)} required />
            <input type="password" placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} required />
            <button type="submit">Sign Up</button>
          </form>
        </div>
        <div className={`${styles.formContainer} ${styles.signInContainer}`}>
          <form onSubmit={handleLogin}>
            <h1>Login</h1>
            <input type="email" placeholder="Email" value={loginEmail} onChange={(e) => setLoginEmail(e.target.value)} required/>
            <input type="password" placeholder="Password" value={loginPassword} onChange={(e) => setLoginPassword(e.target.value)} required/>
            <button type="submit">Log In</button>
          </form>
        </div>
        <div className={styles.overlayContainer}>
          <div className={styles.overlay}>
            <div className={`${styles.overlayPanel} ${styles.overlayLeft}`}>
              <h1>Welcome Back!</h1>
              <p>To see the weather, please log in</p>
              <button className={styles.ghost} onClick={() => setIsSignUpActive(false)}>Sign In</button>
            </div>
            <div className={`${styles.overlayPanel} ${styles.overlayRight}`}>
              <h1>Hello, Friend!</h1>
              <p>Enter your details to start your journey</p>
              <button className={styles.ghost} onClick={() => setIsSignUpActive(true)}>Sign Up</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};


const ForecastPage = ({ locationData }) => {
  const [forecastData, setForecastData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!locationData) return;
    const { lat, lon } = locationData.location_coords || { lat: null, lon: null };
    if (!lat || !lon) { setError("Coordinates not available."); setIsLoading(false); return; }

    fetch(`https://weather-app-1-6zck.onrender.com/api/forecast?lat=${lat}&lon=${lon}`)
      .then(res => res.ok ? res.json() : Promise.reject(`API Error: ${res.status}`))
      .then(data => {
        if (data.error) throw new Error(data.error);
        setForecastData(data.forecast);
      })
      .catch(err => setError(err.message))
      .finally(() => setIsLoading(false));
  }, [locationData]);

  if (isLoading) return <div className={styles.statusText}>🧠 Loading forecast...</div>;
  if (error) return <div className={styles.statusText}>⚠️ {error}</div>;
  if (!forecastData) return <div className={styles.statusText}>No forecast data available.</div>;

  const chartLabels = forecastData.map(item => new Date(item.date).toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' }));
  const chartAQIData = forecastData.map(item => item.predicted_aqi);

  const data = {
    labels: chartLabels,
    datasets: [{
      label: 'Predicted AQI',
      data: chartAQIData,
      borderColor: '#818cf8',
      backgroundColor: 'rgba(129, 140, 248, 0.2)',
      fill: true,
      tension: 0.4,
    }],
  };

  const options = {
    responsive: true,
    plugins: { legend: { display: false } },
    scales: {
      y: { ticks: { color: '#e0e0e0' }, grid: { color: 'rgba(255, 255, 255, 0.1)' } },
      x: { ticks: { color: '#e0e0e0' }, grid: { color: 'rgba(255, 255, 255, 0.1)' } },
    },
  };

  return (
    <div className={styles.pageContent}>
      <header className={styles.header}>
        <h1>AQI Forecast</h1>
        <p className={styles.subtitle}>Next 30 Days Prediction</p>
      </header>
      <div className={styles.chartContainer}>
        <Line options={options} data={data} />
      </div>
      <p className={styles.stationText}>Note: This forecast is generated by a predictive model and may differ from official reports.</p>
    </div>
  );
};

// --- Rest of your components remain unchanged ---
const getWeatherBackgroundVideo = (code, isDay) => {
    if (!isDay) return 'night.mp4';
    switch (code) {
        case 1000: return 'sunny.mp4';
        case 1003: case 1006: case 1009: return 'cloudy.mp4';
        case 1030: case 1135: case 1147: return 'misty.mp4';
        case 1063: case 1180: case 1183: case 1186: case 1189: case 1192: case 1195: case 1240: case 1243: case 1246: return 'rainy.mp4';
        case 1066: case 1210: case 1213: case 1216: case 1219: case 1222: case 1225: return 'snowy.mp4';
        case 1087: case 1273: case 1276: return 'stormy.mp4';
        default: return 'day.mp4';
    }
};

const NavItem = ({ icon: Icon, label, isActive, onClick }) => (
    <button className={`${styles.navItem} ${isActive ? styles.active : ''}`} onClick={onClick}>
        {isActive && <div className={styles.activeBar} />}
        <Icon size={24} />
        <span>{label}</span>
    </button>
);

const AqiCard = ({ station }) => {
    let levelClass = '', levelText = '';
    const aqi = Number(station.aqi);
    if (aqi <= 50) { levelClass = styles.good; levelText = 'Good'; }
    else if (aqi <= 100) { levelClass = styles.moderate; levelText = 'Moderate'; }
    else if (aqi <= 150) { levelClass = styles.unhealthySensitive; levelText = 'Unhealthy for Sensitive'; }
    else { levelClass = styles.unhealthy; levelText = 'Unhealthy'; }
    return (
        <div className={styles.aqiCard}>
            <p><strong>AQI:</strong> {station.aqi}</p>
            <p className={`${styles.level} ${levelClass}`}>{levelText}</p>
            <p className={styles.stationLocation}>{station.name}</p>
        </div>
    );
};

const CameraPage = ({ aqiData }) => {
    const videoRef = useRef(null);
    useEffect(() => {
        let stream = null;
        const startCamera = async () => {
            try {
                if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
                    stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } });
                    if (videoRef.current) { videoRef.current.srcObject = stream; }
                }
            } catch (error) { console.error("Error accessing camera:", error); }
        };
        startCamera();
        return () => { if (stream) { stream.getTracks().forEach(track => track.stop()); }};
    }, []);
    if (!aqiData) return <div className={styles.statusText}>Loading AQI Data...</div>;
    let levelClass = '';
    const aqi = Number(aqiData.aqi);
    if (aqi <= 50) levelClass = styles.good;
    else if (aqi <= 100) levelClass = styles.moderate;
    else if (aqi <= 150) levelClass = styles.unhealthySensitive;
    else levelClass = styles.unhealthy;
    const { pollutants = {} } = aqiData;
    return (
        <div className={styles.cameraWrapper}>
            <video ref={videoRef} autoPlay playsInline className={styles.cameraFeed}></video>
            <div className={`${styles.aqiOverlay} ${levelClass}`}>
                <div className={styles.overlayAqiValue}>{aqiData.aqi}</div>
                <div className={styles.overlayAqiText}>{aqiData.advice}</div>
                <div className={styles.pollutantGrid}>
                    {pollutants.pm25 && <div><span>PM2.5</span>{pollutants.pm25}</div>}
                    {pollutants.pm10 && <div><span>PM10</span>{pollutants.pm10}</div>}
                    {pollutants.o3 && <div><span>Ozone</span>{pollutants.o3}</div>}
                    {pollutants.no2 && <div><span>NO₂</span>{pollutants.no2}</div>}
                    {pollutants.so2 && <div><span>SO₂</span>{pollutants.so2}</div>}
                </div>
            </div>
        </div>
    );
};



const AqiPage = ({ data, location }) => {
    if (!data || !location) return null;
    const { pollutants = {} } = data;
    const [searchQuery, setSearchQuery] = useState('');
    const [searchResults, setSearchResults] = useState([]);
    const [isSearching, setIsSearching] = useState(false);
    const handleSearch = (e) => {
        e.preventDefault();
        if (!searchQuery.trim()) return;
        setIsSearching(true);
        setSearchResults([]);
        fetch(`https://weather-app-1-6zck.onrender.com/api/search-aqi?keyword=${searchQuery}`)
            .then(res => res.json())
            .then(data => { setSearchResults(data); setIsSearching(false); })
            .catch(err => { console.error("Search failed:", err); setIsSearching(false); });
    };
    return (
        <div className={styles.pageContent}>
            <header className={styles.header}><h1>{location.town}</h1><p className={styles.subtitle}>{location.district}</p></header>
            <main className={styles.mainContent}>
                <div className={styles.currentWeather}><p>LIVE AIR QUALITY INDEX</p><h2 className={styles.liveAqiValue}>{data.aqi}</h2><p className={styles.advice}>{data.advice}</p><p className={styles.subtitle}>PM2.5: {pollutants.pm25 || 'N/A'}</p></div>
                <div className={styles.forecastGrid}><div className={styles.forecastCard}><p>PM10</p><span>{pollutants.pm10 || 'N/A'}</span></div><div className={styles.forecastCard}><p>Ozone (O₃)</p><span>{pollutants.o3 || 'N/A'}</span></div><div className={styles.forecastCard}><p>SO₂</p><span>{pollutants.so2 || 'N/A'}</span></div><div className={styles.forecastCard}><p>NO₂</p><span>{pollutants.no2 || 'N/A'}</span></div></div>
                <p className={styles.stationText}>Station: {data.station}</p>

                <div className={styles.nearbySection}>
                    <form onSubmit={handleSearch}><div className={styles.searchBox}><Search size={18} className={styles.searchIcon} /><input type="text" placeholder="Search for any location..." value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} /></div></form>
                    {isSearching && <p>Searching...</p>}
                    {searchResults.length > 0 && (<div><h3 className={styles.listTitle}>Results for "{searchQuery}"</h3>{searchResults.map(station => <AqiCard key={station.uid} station={station} />)}</div>)}
                    {!isSearching && searchResults.length === 0 && searchQuery && ( <p>No stations found for "{searchQuery}".</p> )}
                </div>
            </main>
        </div>
    );
};

const WeatherPage = ({ weatherData, aqiData }) => {
    if (!weatherData || !aqiData) return null;
    const { current, astro, hourly } = weatherData;
    return (
        <div className={styles.pageContent}>
            <header className={styles.header}><h2 className={styles.weatherHeaderTemp}>{Math.round(current.temp)}°C</h2><p className={styles.weatherHeaderDesc}>{current.description}</p></header>
            <div className={styles.hourlyContainer}>{hourly.map((hour, index) => ( <div key={index} className={styles.hourItem}><span>{new Date(hour.time * 1000).toLocaleTimeString('en-US', { hour: 'numeric', hour12: true })}</span><img src={`https:${hour.icon}`} alt="" /><span>{Math.round(hour.temp)}°</span></div> ))}</div>
            <div className={styles.detailsGrid}><div className={styles.detailItem}><Sunrise size={24} /><div><p>Sunrise</p><span>{astro.sunrise}</span></div></div><div className={styles.detailItem}><Sunset size={24} /><div><p>Sunset</p><span>{astro.sunset}</span></div></div><div className={styles.detailItem}><Droplets size={24} /><div><p>Humidity</p><span>{current.humidity}%</span></div></div><div className={styles.detailItem}><Wind size={24} /><div><p>Wind</p><span>{current.wind_kph} km/h</span></div></div><div className={styles.detailItem}><Thermometer size={24} /><div><p>UV Index</p><span>{current.uv}</span></div></div><div className={styles.detailItem}><AlertTriangle size={24} /><div><p>AQI</p><span>{aqiData.aqi}</span></div></div></div>
        </div>
    );
};

const ProfilePage = ({ user, onLogout }) => {
    const options = ["Personal Information", "Notifications", "Privacy and Data", "Help Center", "About"];
    return (
        <div className={styles.pageContent}>
            <header className={styles.profileHeader}><h1>PROFILE</h1></header>
            <h2 className={styles.sectionTitle}>Account Centre</h2>
            <div className={styles.profileCard}><div className={styles.profileIcon}>{user.name.charAt(0)}</div><div className={styles.profileInfo}><p className={styles.name}>{user.name}</p><p className={styles.email}>{user.email}</p></div></div>
            <div className={styles.optionList}>{options.map(option => (<div key={option} className={styles.optionItem}>{option}<ChevronRight size={20} opacity={0.5} /></div>))}<div key="Logout" className={styles.optionItem} onClick={onLogout}>Log Out<ChevronRight size={20} opacity={0.5} /></div></div>
        </div>
    );
};

const TripPlannerPage = () => {
    const mapRef = useRef(null);
    const [start, setStart] = useState('');
    const [destination, setDestination] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState(null);
    const [routes, setRoutes] = useState(null);
    const [routeInfo, setRouteInfo] = useState('');
    useEffect(() => {
        if (!mapRef.current) {
            const map = L.map('trip-map-container').setView([20.5937, 78.9629], 4);
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { attribution: '&copy; OpenStreetMap' }).addTo(map);
            mapRef.current = map;
        }
    }, []);
    useEffect(() => {
        if (routes && mapRef.current) {
            const map = mapRef.current;
            map.eachLayer(layer => { if (layer instanceof L.GeoJSON || layer instanceof L.CircleMarker) map.removeLayer(layer); });
            const standardRouteLayer = L.geoJSON(routes.standard_route, { style: { color: '#3b82f6', weight: 6, opacity: 0.8 } }).addTo(map);
            if(routes.warning) {
                alert(routes.warning);
                setRouteInfo('');
            } else if (JSON.stringify(routes.standard_route) === JSON.stringify(routes.clean_route)) {
                setRouteInfo('The fastest route already has the best air quality.');
            } else {
                L.geoJSON(routes.clean_route, { style: { color: '#22c55e', weight: 6, opacity: 0.8 } }).addTo(map);
                setRouteInfo('The green route is recommended for cleaner air, avoiding polluted zones.');
            }
            routes.stations.forEach(station => {
                let color = station.aqi > 100 ? '#ef4444' : '#f59e0b';
                L.circleMarker([station.lat, station.lon], { radius: 5, color, fillColor: color, fillOpacity: 1 }).addTo(map).bindPopup(`AQI: ${station.aqi}`);
            });
            const bounds = standardRouteLayer.getBounds();
            if(bounds.isValid()) map.fitBounds(bounds, { padding: [50, 50] });
        }
    }, [routes]);
    const handleFindRoute = (e) => {
        e.preventDefault();
        if (!start || !destination) { setError("Please enter both a start and destination."); return; }
        setIsLoading(true);
        setError(null);
        setRoutes(null);
        setRouteInfo('');
        fetch(`https://weather-app-1-6zck.onrender.com/api/clean-route?start=${start}&end=${destination}`)
            .then(res => res.json())
            .then(data => {
                if (data.error) throw new Error(data.error);
                setRoutes(data);
                setIsLoading(false);
            })
            .catch(err => { setError(`Failed to find routes: ${err.message}`); setIsLoading(false); });
    };
    return (
        <div className={styles.pageContent}>
            <header className={styles.header}><h1>Clean Air Route Planner</h1></header>
            <form className={styles.tripForm} onSubmit={handleFindRoute}><input type="text" value={start} onChange={e => setStart(e.target.value)} placeholder="Starting location..." /><input type="text" value={destination} onChange={e => setDestination(e.target.value)} placeholder="Destination..." /><button type="submit" disabled={isLoading}>{isLoading ? "Finding..." : "Find Route"}</button></form>
            {error && <p className={styles.errorText}>{error}</p>}
            <div id="trip-map-container" className={styles.mapContainer}></div>
            {routes && (
                <div className={styles.legendContainer}>
                    <div className={styles.legend}>
                        <div><span style={{backgroundColor: '#3b82f6'}}></span> Standard Route</div>
                        {!routes.warning && JSON.stringify(routes.standard_route) !== JSON.stringify(routes.clean_route) && <div><span style={{backgroundColor: '#22c55e'}}></span> Cleaner Route</div>}
                    </div>
                    {routeInfo && <p className={styles.routeInfo}>{routeInfo}</p>}
                </div>
            )}
        </div>
    );
};


const AqiScreen = () => {
  const [user, setUser] = useState(null);
  const [activeScreen, setActiveScreen] = useState('AQI');
  const [locationData, setLocationData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [backgroundVideo, setBackgroundVideo] = useState('day.mp4');

  useEffect(() => {
    const storedUser = localStorage.getItem('weatherAppUser');
    if (storedUser) setUser(JSON.parse(storedUser));
    else setIsLoading(false);
  }, []);

  useEffect(() => {
    if (!user) return;
    let watchId = null;
    const fetchDataForPosition = (position) => {
      const { latitude, longitude } = position.coords;
      setIsLoading(true);

      fetch(`https://weather-app-1-6zck.onrender.com/api/live-data?lat=${latitude}&lon=${longitude}`)
        .then(res => res.ok ? res.json() : Promise.reject(`API Error: ${res.status}`))
        .then(mainData => {
          if (mainData.error) throw new Error(mainData.error);
          setLocationData({ ...mainData, location_coords: { lat: latitude, lon: longitude } });
          const { weatherCode, isDay } = { weatherCode: mainData.weatherData.current.condition_code, isDay: mainData.weatherData.current.is_day };
          setBackgroundVideo(getWeatherBackgroundVideo(weatherCode, isDay));
          setError(null);
        })
        .catch(err => setError(err.message))
        .finally(() => setIsLoading(false));
    };

    const handleGeoError = (geoError) => { setError(`Location Error: ${geoError.message}`); setIsLoading(false); };
    watchId = navigator.geolocation.watchPosition(fetchDataForPosition, handleGeoError, { enableHighAccuracy: true });
    return () => { if (watchId) navigator.geolocation.clearWatch(watchId); };
  }, [user]);

  const handleLogout = () => { setUser(null); setLocationData(null); setActiveScreen('AQI'); };

  const renderMainApp = () => {
    if (isLoading && !locationData) return <div className={styles.statusText}>🛰️ Fetching live data...</div>;
    if (error) return <div className={styles.statusText}>⚠️ {error}</div>;
    if (!locationData && user) return <div className={styles.statusText}>Awaiting location permissions...</div>;

    switch(activeScreen) {
      case 'AQI': return <AqiPage data={locationData.aqiData} location={locationData.location} />;
      case 'Weather': return <WeatherPage weatherData={locationData.weatherData} aqiData={locationData.aqiData} />;
      case 'Map': return <TripPlannerPage />;
      case 'Camera': return <CameraPage aqiData={locationData.aqiData} />;
      case 'Forecast': return <ForecastPage locationData={locationData} />;
      case 'Profile': return <ProfilePage user={user} onLogout={handleLogout} />;
      default: return null;
    }
  };

  if (!user) return <LoginSignUpPage onLogin={(loggedInUser) => { setUser(loggedInUser); setIsLoading(true); }} />;

  return (
    <div className={styles.container}>
      <div className={styles.screen}>
        {activeScreen !== 'Profile' && activeScreen !== 'Camera' && activeScreen !== 'Forecast' &&
          <video key={backgroundVideo} autoPlay loop muted className={styles.backgroundVideo}><source src={backgroundVideo} type="video/mp4" /></video>
        }
        {renderMainApp()}
        <nav className={styles.navBar}>
          <NavItem icon={SlidersHorizontal} label="AQI" isActive={activeScreen === 'AQI'} onClick={() => setActiveScreen('AQI')} />
          <NavItem icon={Sun} label="Weather" isActive={activeScreen === 'Weather'} onClick={() => setActiveScreen('Weather')} />
          <NavItem icon={LineChart} label="Forecast" isActive={activeScreen === 'Forecast'} onClick={() => setActiveScreen('Forecast')} />
          <NavItem icon={MapIcon} label="Map" isActive={activeScreen === 'Map'} onClick={() => setActiveScreen('Map')} />
          <NavItem icon={Camera} label="Camera" isActive={activeScreen === 'Camera'} onClick={() => setActiveScreen('Camera')} />
          <NavItem icon={User} label="Profile" isActive={activeScreen === 'Profile'} onClick={() => setActiveScreen('Profile')} />
        </nav>
      </div>
    </div>
  );
};

export default AqiScreen;
