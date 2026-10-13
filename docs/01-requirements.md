# Requirements

## Purpose

Checkpoint Games is a single-location store that buys, trades, and sells new and used video games, consoles, and accessories. The database records what the store carries, how many of each item are on hand and in what condition, who sells items to the store, who belongs to the loyalty program, and every sale and trade-in. Store staff use it in three roles: clerks run the register, managers watch stock and members, and analysts study sales.

## Scope

**In scope:** the product catalog, stock by condition, customers and loyalty members, sales, and trade-ins.

**Out of scope:** ordering from suppliers, returns and refunds, sales tax, store credit, staff accounts and passwords, more than one store, online sales, and tracking individual copies by serial number.

## Business Rules

Each rule has an ID so the design documents can refer to it.

### Catalog

- **BR-01** The store sells three kinds of products: games, consoles, and accessories. Every product is exactly one of these kinds.
- **BR-02** Every product has a name, a brand (the publisher or manufacturer), and a release year.
- **BR-03** A platform is a family of game systems, such as PlayStation 4 or Nintendo Switch. Each platform has a unique name, a manufacturer, and a release year.
- **BR-04** Each game runs on exactly one platform. A title released for several platforms is a separate product for each one. A platform can have many games.
- **BR-05** Each game has an ESRB rating, except games released before the ESRB began rating games in 1994, which have none.
- **BR-06** A game can belong to one or more genres.
- **BR-07** Each console product is one hardware model of one platform and is identified by its model number. The console's storage capacity is recorded when it has built-in storage.
- **BR-08** Each accessory has a type: controller, cable, memory card, headset, or other.

### Stock

- **BR-09** Stock is counted per product and condition. The conditions are New, Used – Complete (with its original box and parts), and Used – Loose (the item alone). A product can have one stock record for each condition.
- **BR-10** Each stock record has its own selling price and a reorder threshold, the quantity at or below which the item should be restocked.
- **BR-11** Each used stock record has a trade-in value: the amount the store pays a customer for one unit. New stock records have no trade-in value, because the store does not buy new items from customers.
- **BR-12** The quantity on hand can never be negative, so the store cannot sell more units than it has.

### Customers and Loyalty Program

- **BR-13** The store records a customer only when that person sells items to the store or joins the loyalty program. Customers who only buy are not recorded.
- **BR-14** A recorded customer gives a first name, a last name, and a phone number. Each phone number belongs to one customer record, so a returning seller is found by phone instead of being recorded twice.
- **BR-15** Every recorded customer is either a loyalty member or a walk-in seller, never both. A walk-in seller who joins the program keeps the same customer record.
- **BR-16** A loyalty member has a join date, an expiry date, and optionally an email address. Membership lasts one year, and a renewal moves the expiry date forward one year.
- **BR-17** A member is active from the join date up to, but not including, the expiry date.

### Sales

- **BR-18** A sale has a date and time and one or more lines. Each line names one stock record (a product in one condition), the quantity sold, and the unit price charged.
- **BR-19** The unit price is recorded on each line when the sale is made, so later price changes do not change past sales.
- **BR-20** A sale is linked to at most one loyalty member, and only when the member presents a membership at the register.
- **BR-21** An active member receives 10% off each line. The discount is recorded on the line, and it can never exceed the line's total.
- **BR-22** Each sale is paid in full by one method: cash or card.
- **BR-23** Selling a line lowers the stock on hand for that product and condition by the quantity sold.

### Trade-ins

- **BR-24** A trade-in has a date and time, the customer who sold the items, and one or more lines. Each line names one used stock record, the quantity, and the unit value paid.
- **BR-25** The store accepts only working items, graded Used – Complete or Used – Loose. New items are never accepted in a trade-in.
- **BR-26** Trade-ins are paid in cash. Each trade-in line raises the stock on hand for that product and condition by its quantity.

### Roles

- **BR-27** Clerks look up stock and customers and record sales and trade-ins. Managers also see stock levels against reorder thresholds and membership status. Analysts see sales and stock figures but never customer names or contact details.
