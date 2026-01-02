rm -rf out/
npm run build
rm -rf ../wo_portfolio_diff/wo_portfolio_diff/portfolio_diff/
mkdir ../wo_portfolio_diff/wo_portfolio_diff/portfolio_diff/
cp -r out/ ../wo_portfolio_diff/wo_portfolio_diff/portfolio_diff/