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
        bot.waitForChunksToLoad().then(() => {
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

    return new Promise((resolve, reject) => {
        bot.once('goal_reached', () => {
            console.log('Bot has reached the goal!');
            resolve();
        });

        bot.once('path_update', (r) => {
            if (r.status === 'noPath') {
                console.log('No path to goal');
                reject(new Error('No path to goal'));
            }
        });

        bot.once('pathfinder_error', (error) => {
            console.error('Pathfinder error:', error);
            reject(error);
        });
    });
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

function calc_distance(pos1, pos2){
    const { x: x1, y: y1, z: z1 } = pos1;
    const { x: x2, y: y2, z: z2 } = pos2;

    return Math.sqrt( 
        Math.pow((x1 - x2), 2) + Math.pow((y1 - y2), 2) + Math.pow((z1 - z2), 2)
    )
}

async function attackEntity(player_name, args){
    const bot = players[player_name];
    const [entityType] = args;

    if(!bot){
        console.log(`error finding a player with nickname ${player_name}`);
        return;
    }

    const entity = bot.nearestEntity(entity => entity.name.toLowerCase() === entityType);
    if(!entity){
        console.log('requested entity was not found');
        return;
    }

    while(calc_distance(entity.position, bot.entity.position) > 2){
        const { x, y, z } = entity.position;
        await move(player_name, [x, z]);
    }

    bot.attack(entity);
}

async function attackPlayer(player_name, args){
    const bot = players[player_name];
    const [attackedPlayerName] = args;

    if(!bot){
        console.log(`error finding a player with nickname ${player_name}`);
        return;
    }
    
    const entity = bot.nearestEntity(entity => entity.type === 'player' && entity.username.toLowerCase() === attackedPlayerName.toLowerCase());
    if(!entity){
        console.log('requested entity was not found');
        return;
    }

    while(calc_distance(entity.position, bot.entity.position) > 2){
        const { x, y, z } = entity.position;
        await move(player_name, [x, z]);
    }

    bot.attack(entity);
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
        case 'attack_entity':
            attackEntity(playerName, args);
            break;
        case 'attack_player':
            attackPlayer(playerName, args);
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
