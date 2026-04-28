import { Component } from '@angular/core';

// Intentional: any usage
function processData(input: any): any {
  return input as any;
}

// Intentional: untyped export (no return type annotation)
export function fetchUser(id: string) {
  return { id, name: 'User' };
}

// Intentional: typed export
export function greet(name: string): string {
  return `Hello, ${name}`;
}

// Intentional: type assertion (non-any)
const result = (fetchUser('1')) as { id: string; name: string };
