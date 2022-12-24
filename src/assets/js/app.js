var app = new Vue({
    el: "#app",
    data: {
        totalMessages: 0,
        messages: [],
        preview: null,
    },

    methods: {
        refresh: () => {
            app.getResource('api/messages')
                .then(data => {
                    app.totalMessages = data.total;
                    app.messages = data.items;
                    app.preview = null;
                });
        },

        backToInbox: () => {
            app.preview = null;
        },

        selectMessage: (message) => {
            app.getResource('api/messages/'+message.ID)
                .then(data => {
                    app.preview = data;
                });
        },

        getSource: (message) => {
            return message.source;
        },

        hasHTML: (message) => {
            // todo htmlは一旦日対応
            return false;
        },

        formatMessagePlain: (body) => {
            var escaped = app.escapeHtml(body);
            var formatted = escaped.replace(/(https?:\/\/)([-[\]A-Za-z0-9._~:/?#@!$()*+,;=%]|&amp;|&#39;)+/g, '<a href="$&" target="_blank">$&</a>');
            return formatted;
        },

        escapeHtml: (html) => {
            var entityMap = {
                '&': '&amp;',
                '<': '&lt;',
                '>': '&gt;',
                '"': '&quot;',
                "'": '&#39;'
            };
            return html.replace(/[&<>"']/g,  (s) => {
                return entityMap[s];
            });
        },

        downloadUrl: (id, filename) => {
            return 'api/download/' + id + '/' + filename;
        },

        downloadEml: (message) => {
            const blob = new Blob([ message.source ], { 'type' : 'application/octet-stream' });
            const name = message.subject + '.eml';

            if (window.navigator.msSaveBlob) { 
                window.navigator.msSaveBlob(blob, name); 
            } else {
                const anchor = document.getElementById('download-eml');

                anchor.href = window.URL.createObjectURL(blob);
                anchor.download = name;
                anchor.click();
            }
        },

        deleteOne: (message) => {
            app.deleteResource('api/messages/'+message.ID)
                .then(() => {
                    app.refresh();
                });
        },


        deleteAllConfirm: () => {
            app.deleteResource('api/messages')
                .then(() => {
                    app.refresh();
                    document.getElementById('confirm-delete-all').checked = false;
                });
        },

        fileSize: (bytes) => {
            return filesize(bytes);
        },

        getResource(url) {
            return fetch(url).then((response) => response.json());
        },

        deleteResource(url) {
            return fetch(url, {method: 'DELETE'});
        }

    },
    mounted() {
        window.onload = () => {
            app.refresh();
        };
    }
});

