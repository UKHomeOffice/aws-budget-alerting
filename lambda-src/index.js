const request = require('request-promise-native')
const os = require('os')

const messageSuffix = os.EOL + os.EOL + 'Please set the alert thresholds to higher values if you want to be notified of overspend again this month'

const sendMessage = (message) => request.post({
  url: process.env.WEBHOOK_URL,
  body: message,
  json: true
})
  .then((body) => {
    if (body === 'ok') {
      return {}
    } else {
      throw new Error(body)
    }
  })

const processRecord = (record) => {
  // Get the message prefix if any (e.g. a human-friendly AWS account name)
  const messagePrefix = process.env.MESSAGE_PREFIX
    ? process.env.MESSAGE_PREFIX + os.EOL
    : ''
  return sendMessage({
    text: `<!here> ${messagePrefix}${record.Sns.Message}${messageSuffix}`
  })
}

exports.handler = (event, context, cb) => {
  if (!process.env.WEBHOOK_URL) {
    throw new Error('WEBHOOK_URL environment variable must be defined')
  }
  console.log(`event received: ${JSON.stringify(event)}`)
  Promise.all(event.Records.map(processRecord))
    .then(() => {
      if (cb) {
        cb(null)
      }
    })
    .catch((err) => {
      if (cb) {
        cb(err)
      }
    })
}
