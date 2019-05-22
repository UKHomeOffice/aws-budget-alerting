const request = require('request-promise-native');

const sendMessage = (message) => request.post({
        url: process.env.WEBHOOK_URL,
        body: message,
        json: true,
    })
    .then((body) => {
        if (body === 'ok') {
            return {};
        } else {
            throw new Error(body);
        }
    });

const processRecord = (record) => sendMessage({
    text: `<!here>  ${record.Sns.Message}`,
});

exports.handler = (event, context, cb) => {
    if (!process.env.WEBHOOK_URL) {
        throw new Error('WEBHOOK_URL environment variable must be defined')
    }
    console.log(`event received: ${JSON.stringify(event)}`);
    Promise.all(event.Records.map(processRecord))
        .then(() =>  {
            if (cb) {
                cb(null)
            }
        })
        .catch((err) => {
            if (cb) {
                cb(err)
            }
        });
};
