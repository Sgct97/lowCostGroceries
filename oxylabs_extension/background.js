// Oxylabs Proxy - Direct mode (not PAC script)
const PROXY_HOST = "isp.oxylabs.io";
const PROXY_PORTS = [8001, 8002, 8003, 8004, 8005, 8006, 8007, 8008, 8009, 8010, 8011, 8012, 8013, 8014, 8015, 8016, 8017, 8018, 8019, 8020];
const PROXY_USER = "lowCostGroceris_26SVt";
const PROXY_PASS = "AppleID_1234";

let portIndex = Math.floor(Math.random() * PROXY_PORTS.length);

function setProxy() {
    const port = PROXY_PORTS[portIndex];
    
    const config = {
        mode: "fixed_servers",
        rules: {
            singleProxy: {
                scheme: "http",
                host: PROXY_HOST,
                port: port
            },
            bypassList: ["localhost", "127.0.0.1"]
        }
    };
    
    chrome.proxy.settings.set(
        { value: config, scope: "regular" },
        () => {
            console.log(`✅ Proxy set: ${PROXY_HOST}:${port}`);
        }
    );
}

function rotateProxy() {
    portIndex = (portIndex + 1) % PROXY_PORTS.length;
    setProxy();
    console.log(`🔄 ROTATED to port ${PROXY_PORTS[portIndex]}`);
}

// Initial setup
setProxy();

// Rotate every 10 seconds
setInterval(rotateProxy, 10000);

// Auth handler
chrome.webRequest.onAuthRequired.addListener(
    (details, callback) => {
        callback({
            authCredentials: {
                username: PROXY_USER,
                password: PROXY_PASS
            }
        });
    },
    { urls: ["<all_urls>"] },
    ["asyncBlocking"]
);

console.log('Oxylabs proxy: Started with rotation');
