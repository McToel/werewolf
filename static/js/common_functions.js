var socket = io();

var username = '';
var role = '';
var last_message = '';

document.addEventListener('DOMContentLoaded', request_game_data, false);

function request_game_data() {
    socket.emit('load_game');
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

function send_msg() {
    socket.emit('send_msg', {
        "target_user": event.target.parentElement['target_user'].value,
        "msg": event.target.parentElement['msg'].value
    })
}

function remove_vote(data) {
    try {
        var vote = document.getElementById(data['voter'] + '_vote');
        vote.remove();
    } catch (error) { }
}

function remove_user(data) {
    try {
        var vote = document.getElementById(data['name'] + '_row');
        vote.remove();
    } catch (error) { }
}

function display_head() {
    document.getElementById("username_head").innerHTML = username;
    document.getElementById("role_head").innerHTML = role;
    document.getElementById("msg_head").innerHTML = last_message;
}

async function flash(flashes, color, time) {
    var main_body = document.getElementById('main_body');
    for (var i = 0; i < flashes; i++) {
        main_body.style.backgroundColor = color;
        await sleep(time);
        main_body.style.backgroundColor = 'white';
        await sleep(time);
    }
}

socket.on('flash', async function () {
    flash(3, 'red', 100)
});

socket.on('append_user', function (data) {
    remove_user(data);
    var new_row = user_table_row(data);
    $('#user_table').append(new_row);
});

socket.on('remove_user', function (data) {
    $('#' + data['target'] + '_row').remove();
});

socket.on('update_vote', function (data) {
    remove_vote(data);

    var votes_div = document.getElementById(data['target'] + '_votes');
    var votes_entry = '<span id="' + data['voter'] + '_vote"><div class="username voter">' + data['voter'] + '</div><br/></span>';
    votes_div.insertAdjacentHTML('beforeend', votes_entry);
});

socket.on('remove_vote', function (data) {
    remove_vote(data)
});

socket.on('set_name', function (data) {
    username = data['name'];
    display_head();
})

socket.on('set_role', function (data) {
    role = data['role'];
    display_head();
})

socket.on('receive_msg', function (data) {
    last_message = data['msg'];
    display_head();
    flash(1, '#adffb6', 50);
});

socket.on('join_role_rooms', function (data) {
    socket.emit('join_role_rooms', data);
});

if (socket)
    socket.emit('get-session');