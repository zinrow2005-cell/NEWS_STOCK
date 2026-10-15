const fs = require('fs'), vm=require('vm'), assert=require('assert');
const s=fs.readFileSync(require('path').join(__dirname,'..','assets','app.js'),'utf8');
const beginning=s.indexOf('var D=(e,t)=>'), ending=s.indexOf('function te(e,t,n,r,i,a,o=',beginning);
if(beginning<0||ending<0)throw Error('missing engine');
const c={};vm.runInNewContext(s.slice(beginning,ending)+';globalThis.testK=k;globalThis.testEE=ee;',c);
const trade=(id,side,date,units,price,brokerId=1,symbol='9802')=>({id,side,tradeDate:date,units,price,brokerId,symbol,stockName:symbol,fee:0,tax:0});
const dividend=(id,cash,ratio=0,exDate='2026-04-01',payDate='2026-04-30',brokerId=1,mode='auto')=>({id,mode,symbol:'9802',stockName:'鈺齊',exDate,paymentDate:payDate,brokerId,cashPerShare:cash,stockPerShare:ratio,actualCashAmount:cash,actualStockUnits:0,reconciledAt:'',reconciledCashAmount:0,reconciledStockUnits:-1});
const result=(trades,divs=[],actions=[],transfers=[],date='2026-10-15')=>c.testEE(trades,divs,actions,date,transfers);
const near=(got,expected)=>assert.ok(Math.abs(got-expected)<1e-5,`${got} vs ${expected}`);
// 1000 shares x 100, 5 cash/share, and 10% share bonus => (100000-5000)/1100
let r=result([trade(1,'opening','2026-01-01',1000,100)],[dividend(1,5,0.1)]).positions[0];
assert.equal(r.units,1100);near(r.cost,100000);near(r.cashDividendCredit,5000);near((r.cost-r.cashDividendCredit)/r.units,95000/1100);
// Sell half of bonus adjusted stock: previous dividend pro-rated for retained shares.
r=result([trade(1,'opening','2026-01-01',1000,100),trade(2,'sell','2026-06-01',550,120)],[dividend(1,5,0.1)]).positions[0];
assert.equal(r.units,550);near(r.cashDividendCredit,2500);near(r.cost,50000);near((r.cost-r.cashDividendCredit)/r.units,95000/1100);
// Bought after ex date => no dividend on those shares.
r=result([trade(1,'opening','2026-01-01',1000,100),trade(2,'buy','2026-04-15',1000,100)],[dividend(1,5)]).positions[0];
assert.equal(r.units,2000);near(r.cashDividendCredit,5000);
// A dividend with future pay date must not discount current break even.
r=result([trade(1,'opening','2026-01-01',1000,100)],[dividend(1,5,0,'2026-04-01','2027-01-01')]).positions[0];
near(r.cashDividendCredit,0);
// Partial broker transfer preserves cash cost basis pro-rata.
r=result([trade(1,'opening','2026-01-01',1000,100)],[dividend(1,5)],[],[{id:1,symbol:'9802',stockName:'鈺齊',fromBrokerId:1,toBrokerId:2,transferDate:'2026-06-01',units:400}]);
near(r.positions[0].cashDividendCredit,5000);near(r.brokerPositions.find(x=>x.brokerId===1).cashDividendCredit,3000);near(r.brokerPositions.find(x=>x.brokerId===2).cashDividendCredit,2000);
// Actual cash, no duplicated stock grant.
r=result([trade(1,'opening','2026-01-01',1000,100)],[dividend(1,3000,0,'2026-04-01','2026-05-01',1,'actual')]).positions[0];
assert.equal(r.units,1000);near(r.cashDividendCredit,3000);
// Dividend issued before the opening stock should not be back-allocated into opening positions.
r=result([trade(1,'opening','2026-05-01',1000,90)],[dividend(1,3000,0,'2025-01-01','2025-03-01',1,'actual')]).positions[0];
near(r.cashDividendCredit,0);
// cash reduction, preserve capital recovery info.
r=result([trade(1,'opening','2026-01-01',1000,100)],[],[{id:1,actionType:'cash_reduction',symbol:'9802',stockName:'鈺齊',actionDate:'2026-05-01',cashPaymentDate:'2026-05-30',reductionRate:0.2,cashPerShare:3,actualCashAmount:0}]).positions[0];
assert.equal(r.units,800);near(r.capitalCredit,3000);near((r.cost-r.capitalCredit)/r.units,97000/800);
// Ex-dividend accrual follows the original entitled shares; post ex-date buys do NOT inherit their cash.
r=result([trade(1,'opening','2026-01-01',1000,100),trade(2,'sell','2026-04-10',800,120),trade(3,'buy','2026-04-20',300,110)],[dividend(1,5,0,'2026-04-01','2026-04-30')]).positions[0];
assert.equal(r.units,500);near(r.cashDividendCredit,1000);
// A transfer between ex-date and payment takes the pending cash credit to its new brokerage.
r=result([trade(1,'opening','2026-01-01',1000,100)],[dividend(1,5,0,'2026-04-01','2026-04-30')],[],[{id:1,symbol:'9802',stockName:'鈺齊',fromBrokerId:1,toBrokerId:2,transferDate:'2026-04-15',units:400}]);
near(r.brokerPositions.find(x=>x.brokerId===1).cashDividendCredit,3000);near(r.brokerPositions.find(x=>x.brokerId===2).cashDividendCredit,2000);
// Competing payouts: one settled, one future, break-even only reflects the settled payout.
r=result([trade(1,'opening','2026-01-01',1000,100)],[dividend(1,5,0,'2026-04-01','2026-04-30'),dividend(2,7,0,'2026-09-01','2026-12-30')]).positions[0];
near(r.cashDividendCredit,5000);
console.log('PASS 11 accounting scenarios: bonus stock, dividends, partial sales, timing, transfers, actual receipts, historical receipts, capital reduction');
