
import { OFFER_TYPE_METADATA } from './frontend/src/features/offer-studio/types/offer-metadata';
import { OfferType } from './frontend/src/lib/api/offer';

console.log("Checking OfferType enum for duplicates...");
const seenValues = new Set();
for (const key in OfferType) {
    const value = OfferType[key];
    if (seenValues.has(value)) {
        console.error(`Duplicate Enum Value found: ${value}`);
    }
    seenValues.add(value);
}

console.log("Checking OFFER_TYPE_METADATA for duplicate values...");
const options = Object.values(OFFER_TYPE_METADATA).map(meta => meta.type);
const seenOptions = new Set();
const duplicates = [];

options.forEach(opt => {
    if (seenOptions.has(opt)) {
        duplicates.push(opt);
    }
    seenOptions.add(opt);
});

if (duplicates.length > 0) {
    console.error("Duplicate options found:", duplicates);
} else {
    console.log("No duplicates found in OFFER_TYPE_METADATA values.");
}

console.log(`Total options: ${options.length}`);
