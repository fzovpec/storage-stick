const mineflayer = require('mineflayer');
const Item = require('prismarine-item')('1.20.1')
const pathfinder = require('mineflayer-pathfinder').pathfinder
const Movements = require('mineflayer-pathfinder').Movements
const { GoalXZ } = require('mineflayer-pathfinder').goals
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

    bot.loadPlugin(pathfinder)
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

async function move(player_name, args){
    const bot = players[player_name];
    if(!bot){
        console.log(`error finding a player with nickname ${player_name}`);
        return
    }

    const [x, z] = args;
    if (!(x && z)){
        console.log('coordinates are not completed')
    }

    const defaultMove = new Movements(bot);
    bot.pathfinder.setMovements(defaultMove);
    bot.pathfinder.setGoal(new GoalXZ(x, z));
}

async function placeBlock(player_name, args){
    const bot = players[player_name];

    let [itemId, x, y, z, xFaceAgainst, yFaceAgainst, zFaceAgainst] = args;
    itemId = Number(itemId);
    if(!bot){
        console.log(`error finding a player with nickname ${player_name}`);
        return
    }
    // in args we gonna need coordinates, block id, and placed against id
    const item = new Item(itemId, 1)
    const inventorySlot = 36;
    console.log(item);

    bot.creative.clearInventory().then(() => {
        bot.creative.setInventorySlot(inventorySlot, item).then(() => {
            const inventoryItem = bot.inventory.findInventoryItem(itemId, null);

            bot.equip(inventoryItem, 'hand').then(() => {
                var targetBlock = bot.blockAt(Vec3(x, y, z));
                bot.placeBlock(targetBlock, new Vec3(0, 1, 0)).then(() => {
                    console.log('success');
                });
            });
        });
    });

}

function handleCommand(action, playerName, args) {
    switch (action) {
        case 'login':
            login(playerName);
            break;
        case 'remove_block':
            removeBlock(playerName, args)
            break;
        case 'move':
            move(playerName, args);
            break;
        case 'place_block':
            placeBlock(playerName, args);
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
