const request = require('request-promise-native');

const sendMessage = (message) => {
    return request.post({
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
};

const processRecord = (record) => {
    return sendMessage({
        text: `<!here>  ${record.Sns.Message}`,
    });
};


//const handler = (event, context, cb) => {
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

//event = {
//    type: 'forecast',
//    budget: '1200',
//    threshold: '80%',
//    msg: 'local node app (testing - not triggered by AWS)'
//}
//handler(event, null, null)
