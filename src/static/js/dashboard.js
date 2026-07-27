//Have the browswer refresh the dashboard
//every 5,000 milliseconds.
const REFRESH_INTERVAL_MS = 5000;

setInterval(() => {
    window.location.reload();
}, REFRESH_INTERVAL_MS);