const mineflayer = require('mineflayer');
const readline = require('readline');
const Vec3 = require('vec3');
const fs = require('fs');
const path = require('path');

const logFilePath = process.argv[2] || path.join(__dirname, 'bot_log.txt');
fs.writeFileSync(logFilePath, '', 'utf8');

const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
    prompt: 'Enter command: '
});

var players = {};

// TODO: Look into dropping of actions that you send to js

async function login(player_name){
    const bot = mineflayer.createBot({
        host: 'localhost',
        username: player_name,
        auth: 'offline'
    });

    players[player_name] = bot;
    
    const startTime = Date.now();
    // TODO: do not use datetime. Use monotonically increasing clock
    console.log('start time');
    
    bot.once("spawn", () => {
        // This is called
        console.log("Spawned");
        
        bot.waitForChunksToLoad().then(() => {
          // This is not called
            const endTime = Date.now();

            fs.appendFileSync(logFilePath, `${player_name} ${endTime - startTime}\n`, 'utf8');
        });
      });
}

async function removeBlock(player_name, args){
    const bot = players[player_name];
    if(!bot){
        console.log(`error finding a player with nickname ${player_name}`);
        return
    }

    if (bot.targetDigBlock) {
        bot.chat(`already digging ${bot.targetDigBlock.name}`)
    } 
    else {
        const [x, y, z] = args;

        if (!(x && y && z)){
            console.log('coordinates are not completed')
        }

        var target = bot.blockAt(Vec3(x, y, z));
        if (target && bot.canDigBlock(target)) {
            bot.chat(`starting to dig ${target.name}`)
            bot.dig(target, onDiggingCompleted)
        } 
        else {
            bot.chat('cannot dig')
        }
    }

    function onDiggingCompleted (err) {
        if (err) {
            console.log(err.stack)
            return
        }
        bot.chat(`finished digging ${target.name}`)
    }
}

function handleCommand(action, playerName, args) {
    switch (action) {
        case 'login':
            login(playerName);
            break;
        case 'remove_block':
            removeBlock(playerName, args)
            break;
        default:
            console.log(`Unknown action: ${action}`);
    }
}

// Listen for commands from the command line
rl.prompt();
rl.on('line', (input) => {
    const [action, playerName, ...args] = input.trim().split(/\s+/);
    if (action && playerName) {
        handleCommand(action, playerName, args);
    } else {
        console.log('Invalid command format. Use: action player_name [arguments...]');
    }
    rl.prompt();
}).on('close', () => {
    console.log('Exiting...');
    process.exit(0);
});
