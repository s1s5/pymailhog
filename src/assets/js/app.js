var app = new Vue({
    el: "#app",
    data: {
        totalMessages: 0,
        messages: [],
        preview: null,
    },

    methods: {
        refresh: function() {
            $.ajax({
                url: 'api/v1/messages'
            }).done(function(data) {
                app.totalMessages = data.total;
                app.messages = data.items;
                app.preview = null;
            });
        },

        backToInbox: function() {
            app.preview = null;
        },

        selectMessage: function(message) {
            $.ajax({
                url: 'api/v1/messages/'+message.ID,
            }).done(function(data) {
                app.preview = data;
            });
        },

        getSource: function(message) {
            return message.source;
        },

        hasHTML: function(message) {
            // todo htmlは一旦日対応
            return false;
        },

        formatMessagePlain: function(body) {
            var escaped = app.escapeHtml(body);
            var formatted = escaped.replace(/(https?:\/\/)([-[\]A-Za-z0-9._~:/?#@!$()*+,;=%]|&amp;|&#39;)+/g, '<a href="$&" target="_blank">$&</a>');
            return formatted;
        },

        escapeHtml: function(html) {
            var entityMap = {
                '&': '&amp;',
                '<': '&lt;',
                '>': '&gt;',
                '"': '&quot;',
                "'": '&#39;'
            };
            return html.replace(/[&<>"']/g, function (s) {
                return entityMap[s];
            });
        },

        downloadUrl: function(id, filename) {
            return 'api/v1/download/' + id + '/' + filename;
        },


        deleteOne: function(message) {
            $.ajax({
                url: 'api/v1/messages/'+message.ID,
                type: 'DELETE'
            }).done(function(data) {
                app.refresh();
            });
        },


        deleteAll: function() {
            $('#confirm-delete-all').modal();
        },

        deleteAllConfirm: function() {
            $.ajax({
                url: 'api/v1/messages',
                type: 'DELETE'
            }).done(function() {
                $('#confirm-delete-all').modal('hide');
                app.refresh();
            });
        },

        fileSize: function(bytes) {
            return filesize(bytes);
        }

    }

});

$(function(){
    app.refresh();
});

