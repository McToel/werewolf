// Vue.component('player_gamemaster', {
//     props: ['name', 'role', 'alive', 'voters'],
//     data: function () {
//         return {
//             message: ''
//         }
//     },
//     methods: {
//         send_message: function(event) {
//             socket.emit('send_msg', {
//                 "target": this.name,
//                 "msg": this.message
//             })
//         },
//         poke: function(event) {
//             socket.emit('poke', {'target': this.name})
//         },
//         kill: function(event) {
//             socket.emit('kill', {'target': this.name})
//         }
//     },
//     template:
// `
// <div style="display: contents;">
//     <!-- Username -->
//     <div class="col1">
//         <div v-if="alive" class="username">{{ name }}</div>
//         <div v-else><del>{{ name }}</del></div>
//     </div>

//     <!-- Role -->
//     <div class="col2"><div>{{ role }}</div></div>

//     <!-- Votes  -->
//     <div class="col3">
//         <div>
//             <div v-for='voter in voters'>
//                 <span>
//                     <div class="username voter"> {{ voter }} </div><br />
//                 </span>
//             </div>
//         </div>
//     </div>

//     <!-- Buttons -->
//     <div class="col4">
//         <div v-if="alive" class="button_container">
//             <button class="pretty_button" type="button" v-on:click="poke"> Poke </button>
//             <button class="pretty_button" type="button" v-on:click="kill"> Kill </button>
//         </div>
//     </div>

//     <!-- Send msg -->
//     <div class="col5">
//         <div>
//             <input v-model="message" class="pretty_textbox" placeholder="message" v-on:keyup.enter="send_message">
//         </div>
//     </div>
// </div>
// `
// })

// Vue.component('player_player', {
//     props: ['name', 'alive', 'voters'],
//     data: function () {
//         return {
//             message: ''
//         }
//     },
//     methods: {
//         send_message: function() {
//             socket.emit('send_msg', {
//                 "target": this.name,
//                 "msg": this.message
//             })
//         },
//         private_vote: function() {
//             socket.emit('private_vote', {'target': this.name})
//         },
//         public_vote: function() {
//             socket.emit('public_votekill', {'target': this.name})
//         }
//     },
//     template:
// `
// <div style="display: contents;">
// <!-- Username -->
// <div class="col1">
//     <div v-if="alive" class="username">{{ name }}</div>
//     <div v-else><del>{{ name }}</del></div>
// </div>
// <!-- vote buttons -->
// <div class="col2">
//     <div v-if="alive" class="button_container">
//         <button class="pretty_button" type="button" v-on:click="private_vote">Private</button>
//         <button class="pretty_button" type="button" v-on:click="public_vote">Public</button>
//     </div>
// </div>
// <!-- votes -->
// <div class="col3">
//     <div v-for='voter in voters'>
//         <span>
//             <div class="username voter"> {{ voter }} </div><br />
//         </span>
//     </div>
// </div>
// <!-- Send msg -->
// <div class="col4">
//     <div>
//         <input v-model="message" class="pretty_textbox" placeholder="message" v-on:keyup.enter="send_message">
//     </div>
// </div>
// </div>
// `
// })

var socket = io();

var role_setter = new Vue({
    el: '#role_setter',
    delimiters: ['[[', ']]'],
    data: { roles: [] },
    methods: {
        add_add: function (event) {
            console.log(event);
            this.roles.push(document.getElementById('role_text_box').value);
            this.$forceUpdate();
        },
        remove: function (event) {
            if ((index = document.getElementById("selected_roles").selectedIndex) !== -1) {
                this.roles.splice(index, 1);
                this.$forceUpdate();
            }
        },
        set_roles: function (event) {
            socket.emit('set_roles', {
                "roles": this.roles
            });
        }
    }
})

// function reset_votes() {
//     socket.emit('reset_votes')
// }

// function kill() {
//     socket.emit('kill', {
//         "target": event.target.parentElement['target'].value
//     })
// }

// function poke() {
//     socket.emit('poke', {
//         "target": event.target.parentElement['target'].value
//     })
// }

var app = new Vue({
    el: '#app',
    delimiters: ['[[', ']]'],
    data: {
        username:'',
        role:'',
        msg:'',
        players:[]
    }
});

// document.addEventListener('DOMContentLoaded', request_game_data, false);

// function request_game_data() {
//     socket.emit('load_game');
// }

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// function send_msg() {
//     socket.emit('send_msg', {
//         "target": event.target.parentElement['target'].value,
//         "msg": event.target.parentElement['msg'].value
//     })
// }

function update(data) {
    if ('username' in data) {
        app.username = data['username']
    }
    if ('role' in data) {
        app.role = data['role']
    }
    if ('msg' in data) {
        app.msg = data['msg']
    }

    if ('full_update' in data) {
        app.players = {}
    }
    for (player in data['players']) {
        if ('role' in data['players'][player] && data['players'][player].role != "") {
            new_role = data['players'][player].role;
        }
        else if (player in app.players) {
            new_role = app.players[player].role;
        }
        else {
            new_role = '';
        }
        app.players[player] = data['players'][player];
        app.players[player].role = new_role;
    }
    app.$forceUpdate()
}

async function flash(flashes, color, time) {
    var main_body = document.getElementById('main_body');
    for (var i = 0; i < flashes; i++) {
        main_body.style.backgroundColor = color;
        await sleep(time);
        main_body.style.backgroundColor = '#212121';
        await sleep(time);
    }
}

socket.on('flash', async function () {
    flash(3, 'red', 100);
});

socket.on('update', function (data) {
    update(data);
});

if (socket)
    socket.emit('get-session');

// function private_vote() {
//     socket.emit('private_vote', {
//         "target": event.target.parentElement['target'].value
//     })
// }

// function public_vote() {
//     socket.emit('public_vote', {
//         "target": event.target.parentElement['target'].value
//     })
// }