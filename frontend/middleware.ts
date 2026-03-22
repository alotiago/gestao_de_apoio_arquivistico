import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

function parseJwtPayload(token: string): Record<string, unknown> | null {
  try {
    const parts = token.split('.');
    if (parts.length !== 3) return null;
    const payload = JSON.parse(
      Buffer.from(parts[1], 'base64url').toString('utf-8')
    );
    return payload;
  } catch {
    return null;
  }
}

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const accessToken = request.cookies.get('access_token')?.value;

  const isProtected =
    pathname.startsWith('/dashboard') || pathname.startsWith('/portal');

  if (!isProtected) return NextResponse.next();

  // Sem token → login
  if (!accessToken) {
    const loginUrl = new URL('/login', request.url);
    loginUrl.searchParams.set('from', pathname);
    return NextResponse.redirect(loginUrl);
  }

  const payload = parseJwtPayload(accessToken);
  const role = (payload?.role as string) || '';

  // Cliente tentando acessar /dashboard → redireciona para /portal
  if (role === 'cliente' && pathname.startsWith('/dashboard')) {
    return NextResponse.redirect(new URL('/portal', request.url));
  }

  // Interno tentando acessar /portal → redireciona para /dashboard
  if (role !== 'cliente' && role && pathname.startsWith('/portal')) {
    return NextResponse.redirect(new URL('/dashboard', request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/dashboard/:path*', '/portal/:path*'],
};
