'use strict';
const Bluebird = require( '../lambda-src/node_modules/bluebird')
var expect = require( '../lambda-src/node_modules/chai' ).expect;

var myLambda = require( '../lambda-src/index' );


const request = require('../lambda-src/node_modules/request-promise-native');

const sinon = require('../lambda-src/node_modules/sinon')



const WEBHOOK_URL = 'http://localhost/test'
let event_message = require( './aws_budgtets_test_message.json' );
// let sandbox = sinon.createSandbox()

// console.log(event_message)
describe('aws-budget-alert-lambda', function() {
    
    it( `should throw error when WEBHOOK_URL environment variable not defined: `, function( done ) {
        var rpStub = sinon.stub(request, 'post'); // mock rp.post() calls

        // calls to rp.post() return a promise that will resolve to an object
        rpStub.returns(Bluebird.resolve('ok'));
        try {
            myLambda.handler( event_message, { /* context */ }, (err, result) => {
                done( error );
            });
        } catch (error) {
            expect( error ).to.exist;
                    
            expect( error.message ).to.equals('WEBHOOK_URL environment variable must be defined');

            done();
        }
        
    });

    it( `should send event message to WEBHOOK_URL when WEBHOOK_URL environment variable defined and no error: `, function( done ) {
        var rpStub = sinon.stub(request, 'post'); // mock rp.post() calls

        // calls to rp.post() return a promise that will resolve to an object
        rpStub.returns(Bluebird.resolve('ok'));
        
        process.env.WEBHOOK_URL = WEBHOOK_URL
       
        myLambda.handler( event_message, { /* context */ }, (err, result) => {
        
            try {
                
                expect( err ).to.not.exist;
                verifyRequestSentToWebhook(rpStub);
                        
                done();
            }
            catch( error ) {
                done( error );
            }
        });


    });

    it( `should throw error when request to WEBHOOK_URL returns error: `, function( done ) {

        var rpStub = sinon.stub(request, 'post'); // mock rp.post() calls

        const expectedErrorMessage = 'Error from WEBHOOK';
        // calls to rp.post() return a promise that will resolve to an object
        rpStub.returns(Bluebird.resolve(expectedErrorMessage));
        // sandbox.stub(process.env, 'WEBHOOK_URL').value(test-webhook-url)
        process.env.WEBHOOK_URL = WEBHOOK_URL
       
        
        myLambda.handler( event_message, { /* context */ }, (error, result) => {
            expect( error ).to.exist;
            expect( error.message ).to.equals(expectedErrorMessage);
            verifyRequestSentToWebhook(rpStub);    
            done();
        });
    });

    afterEach(() => {
        delete process.env.WEBHOOK_URL
        sinon.restore()
      })

});

function verifyRequestSentToWebhook(rpStub) {
    const requestArg = rpStub.getCall(0).args[0];
    expect(requestArg.url).to.equals(WEBHOOK_URL);
    expect(requestArg.body.text).to.equals("<!here>  " + event_message.Records[0].Sns.Message);
    expect(requestArg.json).to.equals(true);
}
