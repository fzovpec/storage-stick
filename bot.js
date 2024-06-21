const mc = require('minecraft-protocol');

function sleep(ms = 0) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

// Get the number of players from command line arguments
const args = process.argv;
const numberOfPlayers = parseInt(args[2], 10); // Convert the third argument to an integer

if (isNaN(numberOfPlayers)) {
  console.error('Please provide a valid number of players as a command line argument.');
  process.exit(1); // Exit the script with an error code
}

const client = mc.createClient({
  host: "localhost",   // optional
  port: 25565,         // set if you need a port that isn't 25565
  username: 'Bot',     // username to join as if auth is `offline`, else a unique identifier for this account. Switch if you want to change accounts
  // version: false,   // only set if you need a specific version or snapshot (ie: "1.8.9" or "1.16.5"), otherwise it's set automatically
  // password: '12345678'  // set if you want to use password-based auth (may be unreliable). If specified, the `username` must be an email
});

let packetTimestamps = [];

client.on('raw', function (ev) {
  const now = Date.now();
  packetTimestamps.push(now);
});

// Function to calculate average time between packets
function calculateAverageInterval() {
  if (packetTimestamps.length < 2) return 0;
  
  let intervals = [];
  for (let i = 1; i < packetTimestamps.length; i++) {
    intervals.push(packetTimestamps[i] - packetTimestamps[i - 1]);
  }

  const totalInterval = intervals.reduce((acc, interval) => acc + interval, 0);
  return totalInterval / intervals.length;
}

// Log the average interval every second
setInterval(() => {
  const avgInterval = calculateAverageInterval();
  console.log(`Average time between packets: ${avgInterval} ms`);
  console.log(`num packets received: ${packetTimestamps.length}`)

  // Reset the timestamps array every second to only calculate over the last second
  packetTimestamps = [];
}, 20000);

async function main() {
  for (let i = 0; i < numberOfPlayers; i++) {
    console.log('Creating client', i + 1);
    mc.createClient({
      host: "localhost",   // optional
      port: 25565,         // set if you need a port that isn't 25565
      username: `Bot_${i}`,  // username to join as if auth is `offline`, else a unique identifier for this account. Switch if you want to change accounts
      // version: false,   // only set if you need a specific version or snapshot (ie: "1.8.9" or "1.16.5"), otherwise it's set automatically
      // password: '12345678' // set if you want to use password-based auth (may be unreliable). If specified, the `username` must be an email
    });
    
    await sleep(500);
  }

  console.log('Success!');
}

main().catch(err => {
  console.error('An error occurred:', err);
});
