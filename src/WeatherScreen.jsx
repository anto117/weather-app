// Weather Screen component (Updated Version)
const WeatherScreen = () => (
  <div className={styles.screen}>
    <div className={styles.header}>
      <h2>Montreal</h2>
      <p>15° | Mostly Clear</p>
    </div>

    <div className={styles.tabs}>
      <button className={styles.activeTab}>Hourly Forecast</button>
      <button>Weekly Forecast</button>
    </div>

    <div className={styles.hourlyForecast}>
      <div className={styles.hour}>
        <p>12 PM</p>
        <div className={styles.icon}>🌤️</div>
        <p>8°</p>
      </div>
      <div className={`${styles.hour} ${styles.now}`}>
        <p>Now</p>
        <div className={styles.icon}>🌧️</div>
        <p>7°</p>
      </div>
      <div className={styles.hour}>
        <p>2 PM</p>
        <div className={styles.icon}>🌦️</div>
        <p>6°</p>
      </div>
      <div className={styles.hour}>
        <p>3 PM</p>
        <div className={styles.icon}>🌧️</div>
        <p>6°</p>
      </div>
      <div className={styles.hour}>
        <p>4 PM</p>
        <div className={styles.icon}>🌧️</div>
        <p>5°</p>
      </div>
    </div>

    <div className={styles.cards}>
      <div className={styles.card}>
        <h4>Air Quality</h4>
        <p>3 - Low Health Risk</p>
      </div>
      <div className={styles.card}>
        <h4>UV Index</h4>
        <p>4 - Moderate</p>
      </div>
      <div className={styles.card}>
        <h4>Sunrise</h4>
        <p>5:28 AM</p>
        <small>Sunset: 7:25 PM</small>
      </div>
      <div className={styles.card}>
        <h4>Wind</h4>
        <p>9.7 km/h</p>
      </div>
    </div>
  </div>
);