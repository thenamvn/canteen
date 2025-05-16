// GSAP Animations
document.addEventListener('DOMContentLoaded', () => {
    // Hero Section Animation
    gsap.from('#hero .z-10 > *', {
        opacity: 0,
        y: 50,
        rotateX: 20,
        stagger: 0.2,
        duration: 1,
        ease: 'power3.out',
    });

    // Categories Scroll Animation
    gsap.from('#categories .flip-card', {
        scrollTrigger: {
            trigger: '#categories',
            start: 'top 80%',
        },
        opacity: 0,
        y: 100,
        rotateX: 30,
        stagger: 0.1,
        duration: 0.8,
        ease: 'power2.out',
    });

    // Products Scroll Animation
    gsap.from('#featured-products .tilt-card', {
        scrollTrigger: {
            trigger: '#featured-products',
            start: 'top 80%',
        },
        opacity: 0,
        y: 100,
        rotateX: 30,
        stagger: 0.1,
        duration: 0.8,
        ease: 'power2.out',
    });

    // Pagination Scroll Animation
    gsap.from('.flex.space-x-2 li', {
        scrollTrigger: {
            trigger: '.flex.space-x-2',
            start: 'top 90%',
        },
        opacity: 0,
        scale: 0.8,
        rotateX: 20,
        stagger: 0.05,
        duration: 0.6,
        ease: 'back.out(1.7)',
    });
});