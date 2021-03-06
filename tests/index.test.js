'use strict'
const os = require('os')
const Bluebird = require('../lambda-src/node_modules/bluebird')
const expect = require('../lambda-src/node_modules/chai').expect

const myLambda = require('../lambda-src/index')

const request = require('../lambda-src/node_modules/request-promise-native')

const sinon = require('../lambda-src/node_modules/sinon')

const WEBHOOK_URL = 'http://localhost/test'
const MESSAGE_PREFIX = 'Account: MyAccount'
const eventMessage = require('./aws_budgtets_test_message.json')

describe('aws-budget-alert-lambda', function () {
  it(`should throw error when WEBHOOK_URL environment variable not defined: `, function (done) {
    const rpStub = sinon.stub(request, 'post') // mock rp.post() calls

    // calls to rp.post() return a promise that will resolve to an object
    rpStub.returns(Bluebird.resolve('ok'))
    try {
      myLambda.handler(eventMessage, { /* context */ }, (error, result) => {
        expect(error).to.equals(null)
        done(error)
      })
    } catch (error) {
      expect(error).to.not.equals(null)

      expect(error.message).to.equals('WEBHOOK_URL environment variable must be defined')

      done()
    }
  })

  it(`should send event message to WEBHOOK_URL when WEBHOOK_URL environment variable defined and no error: `, function (done) {
    const rpStub = sinon.stub(request, 'post') // mock rp.post() calls

    // calls to rp.post() return a promise that will resolve to an object
    rpStub.returns(Bluebird.resolve('ok'))

    process.env.WEBHOOK_URL = WEBHOOK_URL

    myLambda.handler(eventMessage, { /* context */ }, (err, result) => {
      try {
        expect(err).to.equals(null)
        verifyRequestSentToWebhook(rpStub, '')

        done()
      } catch (error) {
        done(error)
      }
    })
  })

  it(`should send event message to WEBHOOK_URL when WEBHOOK_URL and MESSAGE_PREFIX environment variables defined and no error: `, function (done) {
    const rpStub = sinon.stub(request, 'post') // mock rp.post() calls

    // calls to rp.post() return a promise that will resolve to an object
    rpStub.returns(Bluebird.resolve('ok'))

    process.env.WEBHOOK_URL = WEBHOOK_URL
    process.env.MESSAGE_PREFIX = MESSAGE_PREFIX

    myLambda.handler(eventMessage, { /* context */ }, (err, result) => {
      try {
        expect(err).to.equals(null)
        verifyRequestSentToWebhook(rpStub, MESSAGE_PREFIX)

        done()
      } catch (error) {
        done(error)
      }
    })
  })

  it(`should throw error when request to WEBHOOK_URL returns error: `, function (done) {
    const rpStub = sinon.stub(request, 'post') // mock rp.post() calls

    const expectedErrorMessage = 'Error from WEBHOOK'
    // calls to rp.post() return a promise that will resolve to an object
    rpStub.returns(Bluebird.resolve(expectedErrorMessage))
    // sandbox.stub(process.env, 'WEBHOOK_URL').value(test-webhook-url)
    process.env.WEBHOOK_URL = WEBHOOK_URL

    myLambda.handler(eventMessage, { /* context */ }, (error, result) => {
      try {
        expect(error).to.not.equals(null)
        expect(error.message).to.equals(expectedErrorMessage)
        verifyRequestSentToWebhook(rpStub, '')
        done()
      } catch (error) {
        done(error)
      }
    })
  })

  afterEach(() => {
    delete process.env.WEBHOOK_URL
    delete process.env.MESSAGE_PREFIX
    sinon.restore()
  })
})

function verifyRequestSentToWebhook (rpStub, messagePrefix) {
  const requestArg = rpStub.getCall(0).args[0]
  const expectedBody = '<!here> ' +
                         messagePrefix + (messagePrefix ? os.EOL : '') +
                         eventMessage.Records[0].Sns.Message +
                         os.EOL + os.EOL +
                         'Please set the alert thresholds to higher values if you want to be notified of overspend again this month'
  expect(requestArg.url).to.equals(WEBHOOK_URL)
  expect(requestArg.body.text).to.equals(expectedBody)
  expect(requestArg.json).to.equals(true)
}
