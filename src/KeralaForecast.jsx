import React, { useEffect, useState } from 'react';

const KeralaForecast = () => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("http://127.0.0.1:5000/api/predict_kerala")
      .then(res => res.json())
      .then(resData => {
        setData(resData);
        setLoading(false);
      })
      .catch(err => console.error(err));
  }, []);

  if (loading) return <p>Loading predictions...</p>;

  return (
    <div>
      <h2>Kerala PM2.5 Forecast</h2>
      <table>
        <thead>
          <tr>
            <th>City</th>
            <th>Predicted PM2.5</th>
          </tr>
        </thead>
        <tbody>
          {data.map(item => (
            <tr key={item.City}>
              <td>{item.City}</td>
              <td>{item['PM2.5']}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default KeralaForecast;
